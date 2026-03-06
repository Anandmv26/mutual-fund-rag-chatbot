"""
Tests to ensure the Phase 1 processor correctly chunks raw JSON into the right objects for embedding.
"""
import pytest
import os
import sys

# Ensure root folder is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Phase1_Scraping.ingestion.processor import build_chunks

def test_build_chunks():
    mock_fund = {
        "fund_name": "Test Fund",
        "fund_house": "Test AMC",
        "fund_category": "Equity",
        "sub_category": "Small Cap",
        "fund_manager": "John Doe",
        "nav": "₹ 100",
        "returns_1y": "20%",
        "returns_3y": "15%",
        "returns_5y": "N/A",
        "benchmark": "NIFTY 50",
        "benchmark_comparison": "1Y: 18%",
        "alpha": "2.0",
        "risk_rating": "High",
        "sharpe_ratio": "1.5",
        "expense_ratio": "0.5%",
        "aum": "₹ 1,000 Cr",
        "exit_load": "1%",
        "min_investment": "SIP: 500",
        "lock_in_period": "3 years",
        "source_url": "http://test.com",
        "scraped_at": "2023-01-01T00:00:00Z"
    }

    chunks = build_chunks(mock_fund)
    
    # Assert exactly 3 chunks generated
    assert len(chunks) == 3

    # Assert metadata propagation
    for chunk in chunks:
        assert chunk["metadata"]["fund_name"] == "Test Fund"
        assert chunk["metadata"]["source_url"] == "http://test.com"
        assert chunk["metadata"]["scraped_at"] == "2023-01-01T00:00:00Z"
        assert chunk["metadata"]["fund_category"] == "Equity"
        assert chunk["metadata"]["sub_category"] == "Small Cap"

    # Assert specific chunks strings mapped properly
    # Chunk 1: Profile
    profile = chunks[0]
    assert profile["metadata"]["chunk_type"] == "profile"
    assert "Test Fund is a Equity mutual fund" in profile["text"]
    assert "John Doe" in profile["text"]
    assert "₹ 100" in profile["text"]

    # Chunk 2: Performance
    performance = chunks[1]
    assert performance["metadata"]["chunk_type"] == "performance"
    assert "20%" in performance["text"]
    assert "not available" in performance["text"]  # returns_5y was N/A -> stripped to N/A, fallback happens if value is exact "N/A"
    assert "2.0" in performance["text"]
    assert "NIFTY 50" in performance["text"]

    # Chunk 3: Risk & Cost
    risk = chunks[2]
    assert risk["metadata"]["chunk_type"] == "risk_cost"
    assert "High" in risk["text"]
    assert "0.5%" in risk["text"]
    assert "3 years" in risk["text"]
