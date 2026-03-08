# WealthWise AI: RAG-Powered Mutual Fund Chatbot 🤖📈

WealthWise AI is a high-speed, Retrieval-Augmented Generation (RAG) chatbot designed to answer plain-English questions about specific mutual funds. Built with a focus on accuracy and speed, it extracts live data, builds an in-memory vector index, and leverages Groq's Llama-3 model to provide grounded, hallucination-free answers.

![WealthWise AI](https://mutual-fund-rag-chatbot-eta.vercel.app/og-image.png) <!-- Replace with an actual screenshot if you have one -->

🌐 **Live Demo:** [https://mutual-fund-rag-chatbot-eta.vercel.app/](https://mutual-fund-rag-chatbot-eta.vercel.app/)

## 🚀 Key Features

*   **In-Memory Serverless RAG:** Bypasses traditional database latency and serverless read-only restrictions by generating taking and searching text embeddings entirely in RAM using `FastEmbed` and `NumPy`.
*   **Automated Data Pipeline:** A scheduled GitHub Action runs daily to scrape fresh data from INDmoney, ensuring the bot always has the latest NAVs, AUMs, and returns.
*   **Strict Scope Guarding:** The LLM is heavily prompted to *only* answer questions based on the retrieved context and strictly refuses to provide personal financial advice.
*   **Sub-Second Generation:** Powered by Groq's LPU inference engine for lightning-fast LLM responses.

## 🛠️ Tech Stack

*   **Frontend:** React (Vite), Tailwind CSS (Custom Vanilla CSS), Lucide Icons
*   **Backend:** Python, FastAPI, Uvicorn
*   **AI/RAG:** Groq API (Llama-3.3-70b-versatile), FastEmbed (Sentence Transformers), NumPy
*   **Data Ingestion:** Playwright (Headless Scraping), BeautifulSoup4, Pandas
*   **CI/CD & Deployment:** GitHub Actions (Automated Scraping), Vercel (Serverless Hosting)

## 📚 Source List (INDmoney)

The chatbot currently supports deep-dive Q&A on the following 10 mutual funds, with data aggregated directly from INDmoney public pages:

1.  [DSP World Gold Mining Overseas Equity Omni FoF](https://www.indmoney.com/mutual-funds/equity-funds/dsp-world-gold-fund)
2.  [LIC MF Gold ETF FOF](https://www.indmoney.com/mutual-funds/other-funds/lic-mf-gold-etf-fof)
3.  [ICICI Prudential BHARAT 22 FOF](https://www.indmoney.com/mutual-funds/other-funds/icici-prudential-bharat-22-fof)
4.  [Quant Small Cap Fund](https://www.indmoney.com/mutual-funds/equity-funds/quant-small-cap-fund)
5.  [HDFC Infrastructure Fund](https://www.indmoney.com/mutual-funds/equity-funds/hdfc-infrastructure-fund)
6.  [ICICI Prudential Credit Risk Fund](https://www.indmoney.com/mutual-funds/debt-funds/icici-prudential-regular-savings-fund)
7.  [Kotak Multi Asset Omni FOF](https://www.indmoney.com/mutual-funds/other-funds/kotak-multi-asset-allocator-fof-dynamic)
8.  [Nippon India Multi Asset Allocation Fund](https://www.indmoney.com/mutual-funds/hybrid-funds/nippon-india-multi-asset-allocation-fund)
9.  [Edelweiss Aggressive Hybrid Fund](https://www.indmoney.com/mutual-funds/hybrid-funds/edelweiss-aggressive-hybrid-fund)
10. [Mahindra Manulife Aggressive Hybrid Fund](https://www.indmoney.com/mutual-funds/hybrid-funds/mahindra-manulife-aggressive-hybrid-fund)

## 💬 Sample Q&A

Here are a few examples of accurately grounded questions you can ask the bot:

**Q: What is the 3Y return of Quant Small Cap Fund?**
> **A:** The 3-year return for the Quant Small Cap Fund Growth Option Direct Plan is 31.79%. This fund falls under the Equity category and specifically targets Small Cap investments.

**Q: Who manages the LIC MF Gold ETF?**
> **A:** The LIC MF Gold ETF FOF Direct Growth is managed by Yash Dhoot. He has been managing this fund since July 31, 2023.

**Q: What is the exit load for HDFC Infrastructure Fund?**
> **A:** For the HDFC Infrastructure Fund, an exit load of 1% applies if units in excess of 15% of the investment are redeemed within 1 year. There is no exit load if redeemed after 1 year.

**Q: Should I invest all my money into the DSP World Gold Fund?**
> **A:** I am sorry, but I can only assist with mutual fund-specific details from INDmoney. I cannot provide general advice or personal investment recommendations.

## ⚙️ Local Setup Instructions

To run this project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Anandmv26/mutual-fund-rag-chatbot.git
    cd mutual-fund-rag-chatbot
    ```

2.  **Set up the Backend (FastAPI):**
    ```bash
    cd Phase3_Backend_API
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r ../api/requirements.txt
    ```

3.  **Configure Environment Variables:**
    Create a `.env` file in the root directory and add your Groq API key:
    ```env
    GROQ_API_KEY=your_groq_api_key_here
    VERCEL=  # Leave blank for local dev
    ```

4.  **Run the Backend Server:**
    ```bash
    cd api
    uvicorn main:app --reload --port 8000
    ```

5.  **Run the Frontend (React/Vite):**
    Open a new terminal.
    ```bash
    cd Phase4_Frontend/frontend
    npm install
    npm run dev
    ```
    Access the app at `http://localhost:5173`.

## ⚠️ Disclaimer

**Not Financial Advice:** The information provided by this chatbot is for educational and informational purposes only and does not constitute financial, investment, or legal advice. All data and returns mentioned are based on historical performance scraped from public sources (INDmoney) and are not indicative of future results. Always consult with a qualified financial advisor before making any investment decisions. The creators of this software assume no responsibility for financial losses incurred through the use of this tool.
