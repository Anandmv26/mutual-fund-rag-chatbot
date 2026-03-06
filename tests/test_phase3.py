"""
Phase 3 Tests — FastAPI & Chatbot Logic

Tests the scope guard, grounding, and endpoint responses.
Mocks Groq API to avoid token usage and dependency on key.

Run with: python3.11 -m pytest tests/test_phase3.py -v
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# Path setup
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT_DIR, "Phase3_Backend_API", "api"))

from main import app  # noqa: E402
from core import Phase3Chatbot  # noqa: E402

client = TestClient(app)

# ═══════════════════════════════════════════════════════════════
# 1. CORE LOGIC TESTS
# ═══════════════════════════════════════════════════════════════

class TestScopeGuard:
    """Validate that scope guarding correctly identifies relevant queries."""

    chatbot = Phase3Chatbot()

    def test_in_scope_fund_name(self):
        assert self.chatbot.check_scope("Tell me about Quant Small Cap Fund") is True

    def test_in_scope_nav(self):
        assert self.chatbot.check_scope("What is the current NAV?") is True

    def test_in_scope_returns(self):
        assert self.chatbot.check_scope("highest 3-year return") is True

    def test_out_of_scope_general_advice(self):
        # Queries about generic wealth or stocks without 'fund' keywords
        assert self.chatbot.check_scope("Should I buy Nvidia stock?") is False

    def test_out_of_scope_weather(self):
        assert self.chatbot.check_scope("What is the weather in Mumbai?") is False


class TestGroundingPrompt:
    """Verify that the formatting for grounding is correct."""

    chatbot = Phase3Chatbot()

    def test_includes_all_context_chunks(self):
        chunks = ["Chunk 1: DSP fund details", "Chunk 2: DSP performance info"]
        prompt = self.chatbot.get_grounding_prompt("What is DSP fund?", chunks)
        
        assert "DSP fund details" in prompt
        assert "DSP performance info" in prompt
        assert "Answer in exactly 3 sentences or less" in prompt
        assert "ONLY the context provided" in prompt


# ═══════════════════════════════════════════════════════════════
# 2. ENDPOINT & MOCK TESTS
# ═══════════════════════════════════════════════════════════════

class TestEndpoints:
    """Test FastAPI endpoint responses with mocked Groq core."""

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_suggestions_endpoint(self):
        response = client.get("/suggestions")
        assert response.status_code == 200
        assert "suggestions" in response.json()
        assert len(response.json()["suggestions"]) == 3

    def test_supported_funds_endpoint(self):
        response = client.get("/supported-funds")
        assert response.status_code == 200
        assert "funds" in response.json()
        assert len(response.json()["funds"]) == 10

    @patch("main.chatbot.retriever.search")
    @patch("main.chatbot.client")
    def test_chat_in_scope_mock(self, mock_groq_client, mock_search):
        """Mock the search and Groq call for an in-scope request."""
        # 1. Mock retriever search results
        mock_search.return_value = [
            {
                "id": "dsp_perf",
                "text": "DSP World Gold Mining returns: 1Y: 182.48%, 3Y: 61.74%.",
                "metadata": {"source_url": "https://indmoney.com/dsp", "fund_name": "DSP World Gold"}
            }
        ]
        
        # 2. Mock Groq client completion
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "The fund had high 1Y returns of 182.48%. Research shows it has been volatile."
        mock_groq_client.chat.completions.create.return_value = mock_completion

        # 3. Call the chat endpoint
        response = client.post("/chat", json={"message": "What are the returns for DSP fund?"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_in_scope"] is True
        assert "182.48%" in data["answer"]
        assert data["source_url"] == "https://indmoney.com/dsp"
        assert len(data["suggestions"]) == 3

    def test_chat_out_of_scope(self):
        """Out-of-scope query should not call Groq and should return refusal."""
        response = client.post("/chat", json={"message": "What is the capital of France?"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_in_scope"] is False
        assert "mutual fund-specific details" in data["answer"]
        assert data["source_url"] is None
        assert len(data["suggestions"]) == 3

    def test_chat_invalid_input(self):
        """Invalid schema (missing field) should return 422."""
        response = client.post("/chat", json={})
        assert response.status_code == 422
