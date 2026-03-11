"""
Phase 1 Scraper — INDmoney Mutual Funds
Extracts 15 data points per fund using Playwright + JavaScript evaluation.
Stores each fund as a separate JSON file in data/raw/.
"""
import json
import os
import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright

TARGET_URLS = [
    "https://www.indmoney.com/mutual-funds/dsp-world-gold-mining-overseas-equity-omni-fof-direct-plan-growth-5457",
    "https://www.indmoney.com/mutual-funds/lic-mf-gold-etf-fof-direct-growth-3721",
    "https://www.indmoney.com/mutual-funds/icici-prudential-bharat-22-fof-direct-growth-5380",
    "https://www.indmoney.com/mutual-funds/quant-small-cap-fund-growth-option-direct-plan-611",
    "https://www.indmoney.com/mutual-funds/hdfc-infrastructure-fund-direct-plan-growth-option-3315",
    "https://www.indmoney.com/mutual-funds/icici-prudential-credit-risk-fund-direct-plan-growth-378",
    "https://www.indmoney.com/mutual-funds/kotak-multi-asset-omni-fof-direct-growth-3723",
    "https://www.indmoney.com/mutual-funds/nippon-india-multi-asset-allocation-fund-direct-growth-1005954",
    "https://www.indmoney.com/mutual-funds/edelweiss-aggressive-hybrid-direct-plan-growth-option-4633",
    "https://www.indmoney.com/mutual-funds/mahindra-manulife-aggressive-hybrid-fund-direct-growth-1004900"
]

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "raw")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"


from playwright_stealth import stealth_async

async def scrape_fund(browser, url):
    """Scrape a single fund page and return a clean dictionary."""
    context = await browser.new_context(user_agent=USER_AGENT)
    page = await context.new_page()
    await stealth_async(page)

    try:
        print(f"  → Scraping: {url.split('/')[-1]}")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # Wait for Cloudflare/Bot protection to pass
        fund_name = 'N/A'
        for _ in range(15):
            await asyncio.sleep(2)
            fund_name = await page.evaluate("""() => {
                const h1 = document.querySelector('h1');
                return h1 ? h1.innerText.trim() : 'N/A';
            }""")
            if fund_name != 'N/A' and fund_name.lower() != 'www.indmoney.com':
                break

        if fund_name == 'N/A' or fund_name.lower() == 'www.indmoney.com':
            print(f"  ❌ Blocked or invalid page: {fund_name}")
            return None

        # 2. Fund House (AMC)
        fund_house = await page.evaluate("""() => {
            const link = document.querySelector('a[href*="/mutual-funds/amc/"]');
            return link ? link.innerText.trim() : 'N/A';
        }""")

        # 3. NAV (just the number)
        nav = await page.evaluate("""() => {
            const text = document.body.innerText;
            const match = text.match(/₹([\\d,.]+)/);
            return match ? '₹' + match[1] : 'N/A';
        }""")

        # 4. Risk Rating (from riskometer)
        risk_rating = await page.evaluate("""() => {
            const text = document.body.innerText;
            const match = text.match(/(Very High|High|Moderately High|Moderate|Moderately Low|Low)\\s*Risk/i);
            return match ? match[0] : 'N/A';
        }""")

        # 5. Fund Category (first tag below fund name — Equity, Debt, Hybrid, etc.)
        #    INDmoney shows 3 tags: [Category] | [AMC] | [Sub-category]
        #    e.g. "Equity | DSP Mutual Fund | Global - Other"
        fund_category = await page.evaluate("""() => {
            // Tags are rendered as <a> elements right below the <h1> fund name.
            // Strategy: find the h1, then look for the first sibling/descendant <a>
            // that is NOT the AMC link (amc links contain '/mutual-funds/amc/').
            const h1 = document.querySelector('h1');
            if (!h1) return 'N/A';
            // The tags are typically in the same parent container as the h1.
            const container = h1.parentElement;
            if (!container) return 'N/A';
            const links = container.querySelectorAll('a');
            for (const link of links) {
                const href = link.getAttribute('href') || '';
                const text = link.innerText.trim();
                // Skip the AMC link and empty links
                if (href.includes('/amc/') || !text) continue;
                // The first non-AMC link is the broad category (Equity, Debt, etc.)
                return text;
            }
            return 'N/A';
        }""")

        # 6. Sub-category (third tag — e.g., "Small-Cap", "Global - Other", etc.)
        sub_category = await page.evaluate("""() => {
            const h1 = document.querySelector('h1');
            if (!h1) return 'N/A';
            const container = h1.parentElement;
            if (!container) return 'N/A';
            const links = container.querySelectorAll('a');
            const nonAmc = [];
            for (const link of links) {
                const href = link.getAttribute('href') || '';
                const text = link.innerText.trim();
                if (!href.includes('/amc/') && text) nonAmc.push(text);
            }
            // First tag = category, second non-AMC tag = sub-category
            return nonAmc.length >= 2 ? nonAmc[1] : 'N/A';
        }""")

        # ---------- ALL TABLE ROWS (single extraction) ----------
        # INDmoney renders all data into <tr> elements.
        # We extract ALL rows once, then parse them for each field.
        all_rows = await page.evaluate("""() => {
            const rows = document.querySelectorAll('tr');
            const result = [];
            for (const row of rows) {
                const cells = row.querySelectorAll('td, th');
                const rowData = [];
                for (const cell of cells) rowData.push(cell.innerText.trim());
                if (rowData.length > 0) result.push(rowData);
            }
            return result;
        }""")

        # --- Parse Overview table rows (2-column [label, value] pairs) ---
        def find_overview_value(label):
            """Find value from [label, value] table rows."""
            for row in all_rows:
                if len(row) == 2 and label.lower() in row[0].lower():
                    return row[1]
            return "N/A"

        expense_ratio = find_overview_value("Expense ratio")
        aum = find_overview_value("AUM")
        exit_load = find_overview_value("Exit Load")
        lock_in_period = find_overview_value("Lock In")
        benchmark = find_overview_value("Benchmark")

        # --- Parse Performance table ---
        # Header: [Period, 1M, 3M, 6M, 1Y, 3Y, 5Y]
        # Data:   [This Fund, val, val, val, val, val, val]
        returns_1y = "N/A"
        returns_3y = "N/A"
        returns_5y = "N/A"
        for row in all_rows:
            if len(row) >= 7 and row[0] == "This Fund":
                returns_1y = row[4]  # 1Y
                returns_3y = row[5]  # 3Y
                returns_5y = row[6]  # 5Y
                break

        # --- Parse Peer Comparison table ---
        # Header: [Fund Name, INDmoney Rank, AUM, Expense Ratio, 1Y Returns, 3Y Returns,
        #          3Y Alpha, 3Y Beta, 3Y Sharpe, 3Y Sortino, 3Y Info Ratio]
        # Indices:     0            1           2        3          4           5
        #              6       7        8          9          10
        alpha = "N/A"
        sharpe_ratio = "N/A"
        for row in all_rows:
            if len(row) >= 9 and fund_name and fund_name[:15].lower() in row[0].lower():
                alpha = row[6]
                sharpe_ratio = row[8]
                break

        # (Fund category is now extracted from the header tags above — see step 5)

        # --- Fund Manager (from FAQ answer) ---
        fund_manager = await page.evaluate("""() => {
            const text = document.body.innerText;
            // Pattern 1: FAQ answer "The fund managers are X, Y."
            const faqMatch = text.match(/fund manager[s]? (?:are|is)\\s+(.+?)\\./i);
            if (faqMatch) {
                return faqMatch[1].trim();
            }
            // Pattern 2: Look in table rows for "Fund Manager" label
            const rows = document.querySelectorAll('tr');
            for (const row of rows) {
                const cells = row.querySelectorAll('td');
                if (cells.length === 2 && cells[0].innerText.trim().toLowerCase().includes('fund manager')) {
                    return cells[1].innerText.trim();
                }
            }
            return 'N/A';
        }""")

        # --- Min Investment (Lumpsum & SIP) ---
        min_lumpsum_sip = find_overview_value("Min Lumpsum/SIP")

        # --- Category Index Comparison (from performance table) ---
        # NOTE: This is the category index row (e.g. "Nifty Smallcap 250 Index"),
        # NOT the fund's declared benchmark (e.g. "FTSE Gold Mines TR USD").
        # INDmoney does not show the declared benchmark's returns on the page.
        benchmark_returns = "N/A"
        for row in all_rows:
            if len(row) >= 7 and row[0].endswith("Index"):
                benchmark_returns = f"1Y: {row[4]}, 3Y: {row[5]}, 5Y: {row[6]}"
                break

        # ---------- BUILD CLEAN OUTPUT ----------
        data = {
            "fund_name": fund_name,
            "fund_house": fund_house,
            "fund_category": fund_category,       # Equity, Debt, Hybrid, etc.
            "sub_category": sub_category,          # Small-Cap, Global - Other, etc.
            "fund_manager": fund_manager,
            "nav": nav,
            "returns_1y": returns_1y,
            "returns_3y": returns_3y,
            "returns_5y": returns_5y,
            "benchmark": benchmark,
            "benchmark_comparison": benchmark_returns,  # category index returns, not declared benchmark
            "alpha": alpha,
            "risk_rating": risk_rating,
            "sharpe_ratio": sharpe_ratio,
            "expense_ratio": expense_ratio,
            "aum": aum,
            "exit_load": exit_load,
            "min_investment": min_lumpsum_sip,
            "lock_in_period": lock_in_period,
            "source_url": url,
            "scraped_at": datetime.utcnow().isoformat()
        }

        print(f"  ✅ {fund_name}")
        return data

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None
    finally:
        await page.close()
        await context.close()


async def main():
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        print(f"🚀 Starting scrape of {len(TARGET_URLS)} funds...\n")
        success = 0
        for i, url in enumerate(TARGET_URLS, 1):
            print(f"[{i}/{len(TARGET_URLS)}]")
            fund_data = await scrape_fund(browser, url)
            if fund_data:
                filename = url.split("/")[-1] + ".json"
                filepath = os.path.join(RAW_DATA_DIR, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(fund_data, f, indent=4, ensure_ascii=False)
                print(f"  💾 Saved → {filename}\n")
                success += 1
            else:
                print(f"  ⚠️  Skipped\n")
            await asyncio.sleep(4)

        await browser.close()
        print(f"✨ Done! Successfully scraped {success}/{len(TARGET_URLS)} funds.")
        print(f"📂 Output directory: {RAW_DATA_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
