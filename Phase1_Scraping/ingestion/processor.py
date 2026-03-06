"""
Phase 2 — Processor
Reads raw JSON fund snapshots from data/raw/ and converts them into
semantically meaningful text chunks suitable for embedding.

Chunking Strategy:
  Each fund produces 3 text chunks to stay within the 256-token limit of
  all-MiniLM-L6-v2 while preserving enough context for retrieval:

  1. Fund Profile  — name, house, category, sub-category, manager, NAV, AUM
  2. Performance   — returns (1Y/3Y/5Y), benchmark, benchmark comparison, alpha
  3. Risk & Cost   — risk rating, sharpe ratio, expense ratio, exit load,
                     min investment, lock-in period

  Every chunk is prefixed with the fund name so it remains self-contained.
"""
import json
import os
import glob
from typing import List, Dict, Any

RAW_DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "raw"
)


def load_raw_funds(directory: str = RAW_DATA_DIR) -> List[Dict[str, Any]]:
    """Load all JSON files from the raw data directory."""
    funds = []
    pattern = os.path.join(directory, "*.json")
    for filepath in sorted(glob.glob(pattern)):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["_filepath"] = filepath
            funds.append(data)
    return funds


def _safe(value: Any, fallback: str = "not available") -> str:
    """Return a clean string; replace N/A / null / empty with fallback."""
    if value is None:
        return fallback
    s = str(value).strip()
    if s.lower() in ("n/a", "null", "--", "--/--", ""):
        return fallback
    return s


def build_chunks(fund: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert a single fund dictionary into a list of chunk dicts.
    Each chunk dict contains:
      - text:       the natural-language text to embed
      - metadata:   fund_name, source_url, scraped_at, chunk_type
    """
    name = _safe(fund.get("fund_name"))
    source_url = _safe(fund.get("source_url"), "")
    scraped_at = _safe(fund.get("scraped_at"), "")

    base_meta = {
        "fund_name": name,
        "source_url": source_url,
        "scraped_at": scraped_at,
        "fund_category": _safe(fund.get("fund_category")),
        "sub_category": _safe(fund.get("sub_category")),
    }

    chunks = []

    # ---- 1. Fund Profile ----
    profile_text = (
        f"{name} is a {_safe(fund.get('fund_category'))} mutual fund "
        f"in the {_safe(fund.get('sub_category'))} sub-category, "
        f"managed by {_safe(fund.get('fund_house'))}. "
        f"The fund manager(s): {_safe(fund.get('fund_manager'))}. "
        f"Current NAV is {_safe(fund.get('nav'))} and "
        f"AUM is {_safe(fund.get('aum'))}."
    )
    chunks.append({
        "text": profile_text,
        "metadata": {**base_meta, "chunk_type": "profile"},
    })

    # ---- 2. Performance ----
    perf_text = (
        f"{name} — Performance: "
        f"1-year return {_safe(fund.get('returns_1y'))}, "
        f"3-year return {_safe(fund.get('returns_3y'))}, "
        f"5-year return {_safe(fund.get('returns_5y'))}. "
        f"Benchmark: {_safe(fund.get('benchmark'))}. "
        f"Category index comparison: {_safe(fund.get('benchmark_comparison'))}. "
        f"Alpha: {_safe(fund.get('alpha'))}."
    )
    chunks.append({
        "text": perf_text,
        "metadata": {**base_meta, "chunk_type": "performance"},
    })

    # ---- 3. Risk & Cost ----
    risk_text = (
        f"{name} — Risk & Cost: "
        f"Risk rating is {_safe(fund.get('risk_rating'))}. "
        f"Sharpe ratio: {_safe(fund.get('sharpe_ratio'))}. "
        f"Expense ratio: {_safe(fund.get('expense_ratio'))}. "
        f"Exit load: {_safe(fund.get('exit_load'))}. "
        f"Minimum investment (Lumpsum/SIP): {_safe(fund.get('min_investment'))}. "
        f"Lock-in period: {_safe(fund.get('lock_in_period'))}."
    )
    chunks.append({
        "text": risk_text,
        "metadata": {**base_meta, "chunk_type": "risk_cost"},
    })

    return chunks


def process_all(directory: str = None) -> List[Dict[str, Any]]:
    """
    End-to-end: load every raw JSON → produce all chunks.
    Returns a flat list of chunk dicts.
    """
    if directory is None:
        directory = RAW_DATA_DIR
    funds = load_raw_funds(directory)
    all_chunks = []
    for fund in funds:
        all_chunks.extend(build_chunks(fund))
    return all_chunks


# ---- CLI entry point for manual testing ----
if __name__ == "__main__":
    chunks = process_all()
    print(f"📦 Processed {len(chunks)} chunks from {len(chunks) // 3} funds.\n")
    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i + 1} [{chunk['metadata']['chunk_type']}] ---")
        print(chunk["text"])
        print()
