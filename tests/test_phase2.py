"""
Phase 2 Tests — Processor, Embedder, and Retriever

Run with:  python3.11 -m pytest tests/ -v
"""
import json
import os
import sys
import shutil
import tempfile

import pytest

# ---- Path setup so imports resolve correctly ----
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT_DIR, "Phase1_Scraping", "ingestion"))
sys.path.insert(0, os.path.join(ROOT_DIR, "Phase2_Embedding_Retrieval", "search"))

from processor import load_raw_funds, build_chunks, process_all, _safe  # noqa: E402
from embedder import embed_and_store, get_chroma_client, COLLECTION_NAME  # noqa: E402
from retriever import Retriever  # noqa: E402

# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

SAMPLE_FUND = {
    "fund_name": "Test Equity Growth Fund",
    "fund_house": "Test Mutual Fund",
    "fund_category": "Equity",
    "sub_category": "Large-Cap",
    "fund_manager": "John Doe",
    "nav": "₹150.25",
    "returns_1y": "18.5%",
    "returns_3y": "14.2%",
    "returns_5y": "12.8%",
    "benchmark": "Nifty 50 TR INR",
    "benchmark_comparison": "1Y: 12.1%, 3Y: 11.5%, 5Y: 10.2%",
    "alpha": "2.30",
    "risk_rating": "Very High Risk",
    "sharpe_ratio": "1.45",
    "expense_ratio": "0.85%",
    "aum": "₹5000 Cr",
    "exit_load": "1.0%",
    "min_investment": "₹500/₹500",
    "lock_in_period": "No Lock-in",
    "source_url": "https://www.indmoney.com/mutual-funds/test-fund-123",
    "scraped_at": "2026-03-06T14:00:00.000000",
}

SAMPLE_FUND_DEBT = {
    "fund_name": "Test Bond Debt Fund",
    "fund_house": "Test Debt AMC",
    "fund_category": "Debt",
    "sub_category": "Corporate Bond",
    "fund_manager": "Jane Smith",
    "nav": "₹42.10",
    "returns_1y": "8.5%",
    "returns_3y": "7.2%",
    "returns_5y": "6.8%",
    "benchmark": "CRISIL Composite Bond TR INR",
    "benchmark_comparison": "1Y: 7.0%, 3Y: 6.5%, 5Y: 6.0%",
    "alpha": "1.10",
    "risk_rating": "Moderate Risk",
    "sharpe_ratio": "2.10",
    "expense_ratio": "0.45%",
    "aum": "₹3200 Cr",
    "exit_load": "0.5%",
    "min_investment": "₹1,000/₹500",
    "lock_in_period": "No Lock-in",
    "source_url": "https://www.indmoney.com/mutual-funds/test-debt-fund-456",
    "scraped_at": "2026-03-06T14:00:00.000000",
}


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with sample fund JSONs."""
    tmpdir = tempfile.mkdtemp()
    # Write two sample funds
    for i, fund in enumerate([SAMPLE_FUND, SAMPLE_FUND_DEBT]):
        filepath = os.path.join(tmpdir, f"test-fund-{i}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(fund, f, indent=4, ensure_ascii=False)
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def temp_chroma_dir():
    """Create a temp directory for ChromaDB persistence."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


# ═══════════════════════════════════════════════════════════════
# 1. PROCESSOR TESTS
# ═══════════════════════════════════════════════════════════════

class TestSafeHelper:
    """Tests for _safe() value sanitizer."""

    def test_normal_value(self):
        assert _safe("₹150.25") == "₹150.25"

    def test_na_value(self):
        assert _safe("N/A") == "not available"

    def test_null_string(self):
        assert _safe("null") == "not available"

    def test_dashes(self):
        assert _safe("--") == "not available"

    def test_dashes_pair(self):
        assert _safe("--/--") == "not available"

    def test_none(self):
        assert _safe(None) == "not available"

    def test_empty(self):
        assert _safe("") == "not available"

    def test_custom_fallback(self):
        assert _safe("N/A", "unknown") == "unknown"


class TestBuildChunks:
    """Tests for build_chunks() on a single fund."""

    def test_produces_three_chunks(self):
        chunks = build_chunks(SAMPLE_FUND)
        assert len(chunks) == 3

    def test_chunk_types(self):
        chunks = build_chunks(SAMPLE_FUND)
        types = [c["metadata"]["chunk_type"] for c in chunks]
        assert types == ["profile", "performance", "risk_cost"]

    def test_profile_chunk_content(self):
        chunks = build_chunks(SAMPLE_FUND)
        profile = chunks[0]
        assert "Test Equity Growth Fund" in profile["text"]
        assert "Equity" in profile["text"]
        assert "Large-Cap" in profile["text"]
        assert "Test Mutual Fund" in profile["text"]
        assert "John Doe" in profile["text"]
        assert "₹150.25" in profile["text"]
        assert "₹5000 Cr" in profile["text"]

    def test_performance_chunk_content(self):
        chunks = build_chunks(SAMPLE_FUND)
        perf = chunks[1]
        assert "18.5%" in perf["text"]
        assert "14.2%" in perf["text"]
        assert "12.8%" in perf["text"]
        assert "Nifty 50 TR INR" in perf["text"]
        assert "2.30" in perf["text"]

    def test_risk_chunk_content(self):
        chunks = build_chunks(SAMPLE_FUND)
        risk = chunks[2]
        assert "Very High Risk" in risk["text"]
        assert "1.45" in risk["text"]
        assert "0.85%" in risk["text"]
        assert "1.0%" in risk["text"]
        assert "₹500/₹500" in risk["text"]

    def test_metadata_contains_source_url(self):
        chunks = build_chunks(SAMPLE_FUND)
        for chunk in chunks:
            assert chunk["metadata"]["source_url"] == SAMPLE_FUND["source_url"]

    def test_metadata_contains_fund_category(self):
        chunks = build_chunks(SAMPLE_FUND)
        for chunk in chunks:
            assert chunk["metadata"]["fund_category"] == "Equity"

    def test_handles_missing_fields_gracefully(self):
        """Fund with missing/N/A fields should still produce valid chunks."""
        sparse_fund = {
            "fund_name": "Sparse Fund",
            "fund_house": "N/A",
            "fund_category": None,
            "sub_category": "",
            "nav": "N/A",
        }
        chunks = build_chunks(sparse_fund)
        assert len(chunks) == 3
        # Should contain "not available" instead of N/A
        assert "not available" in chunks[0]["text"]


class TestProcessAll:
    """Tests for process_all() with temp data directory."""

    def test_loads_and_processes_all_funds(self, temp_data_dir):
        chunks = process_all(directory=temp_data_dir)
        # 2 funds × 3 chunks each = 6
        assert len(chunks) == 6

    def test_all_chunks_have_text_and_metadata(self, temp_data_dir):
        chunks = process_all(directory=temp_data_dir)
        for chunk in chunks:
            assert "text" in chunk
            assert "metadata" in chunk
            assert len(chunk["text"]) > 20  # non-trivial text
            assert "fund_name" in chunk["metadata"]
            assert "chunk_type" in chunk["metadata"]


class TestLoadRawFunds:
    """Tests for load_raw_funds()."""

    def test_loads_correct_count(self, temp_data_dir):
        funds = load_raw_funds(temp_data_dir)
        assert len(funds) == 2

    def test_funds_have_filepath(self, temp_data_dir):
        funds = load_raw_funds(temp_data_dir)
        for fund in funds:
            assert "_filepath" in fund
            assert fund["_filepath"].endswith(".json")

    def test_empty_directory(self):
        tmpdir = tempfile.mkdtemp()
        try:
            funds = load_raw_funds(tmpdir)
            assert len(funds) == 0
        finally:
            shutil.rmtree(tmpdir)


# ═══════════════════════════════════════════════════════════════
# 2. EMBEDDER TESTS
# ═══════════════════════════════════════════════════════════════

class TestEmbedder:
    """Tests for embed_and_store()."""

    def test_embeds_all_chunks(self, temp_data_dir, temp_chroma_dir):
        """Should embed exactly 6 chunks (2 funds × 3 each)."""
        # Monkey-patch the processor's data dir
        import processor
        original_dir = processor.RAW_DATA_DIR
        processor.RAW_DATA_DIR = temp_data_dir
        print(f"\nDEBUG: temp_data_dir={temp_data_dir}")
        print(f"DEBUG: temp_chroma_dir={temp_chroma_dir}")

        try:
            count = embed_and_store(
                persist_dir=temp_chroma_dir,
                collection_name="test_funds",
                rebuild=True,
            )
            print(f"DEBUG: embed_and_store returned {count}")
            assert count == 6
        except Exception as e:
            print(f"DEBUG: Exception in test_embeds_all_chunks: {e}")
            raise
        finally:
            processor.RAW_DATA_DIR = original_dir

    def test_rebuild_clears_old_data(self, temp_data_dir, temp_chroma_dir):
        """Rebuild=True should delete and recreate the collection."""
        import processor
        original_dir = processor.RAW_DATA_DIR
        processor.RAW_DATA_DIR = temp_data_dir
        print(f"\nDEBUG: temp_data_dir={temp_data_dir}")
        print(f"DEBUG: temp_chroma_dir={temp_chroma_dir}")

        try:
            # First embed
            embed_and_store(
                persist_dir=temp_chroma_dir,
                collection_name="test_funds",
                rebuild=True,
            )
            # Second embed with rebuild
            count = embed_and_store(
                persist_dir=temp_chroma_dir,
                collection_name="test_funds",
                rebuild=True,
            )
            print(f"DEBUG: embed_and_store (second) returned {count}")
            # Should still be 6, not 12
            client = get_chroma_client(temp_chroma_dir)
            collection = client.get_collection("test_funds")
            current_count = collection.count()
            print(f"DEBUG: collection.count()={current_count}")
            assert current_count == 6
        except Exception as e:
            print(f"DEBUG: Exception in test_rebuild_clears_old_data: {e}")
            raise
        finally:
            processor.RAW_DATA_DIR = original_dir

    def test_upsert_is_idempotent(self, temp_data_dir, temp_chroma_dir):
        """Running embed twice without rebuild should not duplicate chunks."""
        import processor
        original_dir = processor.RAW_DATA_DIR
        processor.RAW_DATA_DIR = temp_data_dir
        print(f"\nDEBUG: temp_data_dir={temp_data_dir}")
        print(f"DEBUG: temp_chroma_dir={temp_chroma_dir}")

        try:
            embed_and_store(
                persist_dir=temp_chroma_dir,
                collection_name="test_funds",
                rebuild=False,
            )
            embed_and_store(
                persist_dir=temp_chroma_dir,
                collection_name="test_funds",
                rebuild=False,
            )
            client = get_chroma_client(temp_chroma_dir)
            collection = client.get_collection("test_funds")
            # Upsert should keep count at 6
            current_count = collection.count()
            print(f"DEBUG: collection.count()={current_count}")
            assert current_count == 6
        except Exception as e:
            print(f"DEBUG: Exception in test_upsert_is_idempotent: {e}")
            raise
        finally:
            processor.RAW_DATA_DIR = original_dir


# ═══════════════════════════════════════════════════════════════
# 3. RETRIEVER TESTS
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def populated_retriever():
    """
    Create a temp ChromaDB with sample data and return a Retriever.
    Uses module scope so embedding only runs once for all retriever tests.
    """
    tmpdir_data = tempfile.mkdtemp()
    tmpdir_chroma = tempfile.mkdtemp()

    # Write sample funds
    for i, fund in enumerate([SAMPLE_FUND, SAMPLE_FUND_DEBT]):
        filepath = os.path.join(tmpdir_data, f"test-fund-{i}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(fund, f, indent=4, ensure_ascii=False)

    # Embed
    import processor
    original_dir = processor.RAW_DATA_DIR
    processor.RAW_DATA_DIR = tmpdir_data

    embed_and_store(
        persist_dir=tmpdir_chroma,
        collection_name="test_retriever",
        rebuild=True,
    )
    processor.RAW_DATA_DIR = original_dir

    retriever = Retriever(
        persist_dir=tmpdir_chroma,
        collection_name="test_retriever",
    )

    yield retriever

    # Cleanup
    shutil.rmtree(tmpdir_data)
    shutil.rmtree(tmpdir_chroma)


class TestRetriever:
    """Tests for Retriever search functionality."""

    def test_collection_count(self, populated_retriever):
        assert populated_retriever.count == 6

    def test_search_returns_results(self, populated_retriever):
        results = populated_retriever.search("equity fund returns", top_k=3)
        assert len(results) > 0
        assert len(results) <= 3

    def test_result_structure(self, populated_retriever):
        results = populated_retriever.search("fund performance", top_k=1)
        r = results[0]
        assert "id" in r
        assert "text" in r
        assert "metadata" in r
        assert "distance" in r
        assert "fund_name" in r["metadata"]
        assert "source_url" in r["metadata"]
        assert "chunk_type" in r["metadata"]

    def test_search_relevance_equity(self, populated_retriever):
        """Query about equity/returns should surface equity fund chunks."""
        results = populated_retriever.search(
            "large cap equity fund with high returns", top_k=3
        )
        # The top result should be from the equity fund
        fund_names = [r["metadata"]["fund_name"] for r in results]
        assert "Test Equity Growth Fund" in fund_names

    def test_search_relevance_debt(self, populated_retriever):
        """Query about debt/bonds should surface debt fund chunks."""
        results = populated_retriever.search(
            "corporate bond debt fund", top_k=3
        )
        fund_names = [r["metadata"]["fund_name"] for r in results]
        assert "Test Bond Debt Fund" in fund_names

    def test_search_relevance_risk(self, populated_retriever):
        """Query about risk/expense should surface risk_cost chunks."""
        results = populated_retriever.search(
            "expense ratio and risk rating", top_k=2
        )
        chunk_types = [r["metadata"]["chunk_type"] for r in results]
        assert "risk_cost" in chunk_types

    def test_category_filter(self, populated_retriever):
        """Filtering by category should only return matching funds."""
        results = populated_retriever.search_by_category(
            query="fund returns",
            category="Debt",
            top_k=4,
        )
        for r in results:
            assert r["metadata"]["fund_category"] == "Debt"

    def test_distance_is_numeric(self, populated_retriever):
        results = populated_retriever.search("any query", top_k=1)
        assert isinstance(results[0]["distance"], float)
        assert results[0]["distance"] >= 0

    def test_top_k_limit_respected(self, populated_retriever):
        results = populated_retriever.search("fund", top_k=2)
        assert len(results) <= 2

    def test_search_with_no_matching_filter(self, populated_retriever):
        """Filter for a non-existent category should return empty."""
        results = populated_retriever.search(
            query="any fund",
            top_k=4,
            where={"fund_category": "Commodities"},
        )
        assert len(results) == 0
