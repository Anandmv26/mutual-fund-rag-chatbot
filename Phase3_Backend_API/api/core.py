import os
import sys
import json
import re
from typing import List, Dict, Any, Optional, Tuple

from groq import Groq
from dotenv import load_dotenv

# Shared logic to resolve Retriever from Phase 2
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "Phase2_Embedding_Retrieval", "search"))
from retriever import Retriever  # noqa: E402

# Load environment variables
load_dotenv()

SUPPORTED_FUNDS = [
    "DSP World Gold Mining Overseas Equity Omni FoF",
    "LIC MF Gold ETF FOF",
    "ICICI Prudential BHARAT 22 FOF",
    "Quant Small Cap Fund",
    "HDFC Infrastructure Fund",
    "ICICI Prudential Credit Risk Fund",
    "Kotak Multi Asset Omni FOF",
    "Nippon India Multi Asset Allocation Fund",
    "Edelweiss Aggressive Hybrid Fund",
    "Mahindra Manulife Aggressive Hybrid Fund"
]

class Phase3Chatbot:
    """RAG-based chatbot logic using Groq and Retriever."""

    def __init__(self, model_id: str = "llama-3.3-70b-versatile"):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_id = os.getenv("LLM_MODEL_ID", model_id)
        if not self.api_key:
            print("[WARNING] GROQ_API_KEY not found in .env! LLM will fail unless mocked.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
        self.retriever = Retriever()

    def get_grounding_prompt(self, user_query: str, context_chunks: List[str]) -> str:
        """Create a prompt that enforces grounding constraints (3 sentences max, no advice)."""
        context_text = "\n---\n".join(context_chunks)
        
        prompt = f"""
### CONTEXT:
{context_text}

### INSTRUCTIONS:
You are a helpful mutual fund information assistant.
Answer the user's question using ONLY the context provided above.
1. Answer in exactly 3 sentences or less.
2. Be technically accurate and precise.
3. If the context does not contain the answer, say 'I'm sorry, I don't have information on that specific fund detail' and stop.
4. DO NOT provide investment advice or personal opinions.
5. Provide ONLY the answer. Do not add 'Based on the context...' or other filler.

USER QUESTION: {user_query}
ANSWER:
"""
        return prompt.strip()

    def check_scope(self, user_query: str) -> bool:
        """A simple keyword/LLM-based scope guard for mutual fund relevance."""
        # First, check if it explicitly mentions any of our supported funds
        for fund in SUPPORTED_FUNDS:
            if fund.lower() in user_query.lower():
                return True
                
        # Simple regex check for mutual fund keywords
        keywords = r"(fund|mutual|equity|debt|hybrid|nav|return|benchmark|expense|aum|risk|exit load|sip|lumpsum|small cap|manager|fof|etf)"
        if re.search(keywords, user_query, re.IGNORECASE):
            return True
        return False

    def generate_suggestions(self, query: str, context: Optional[str] = None) -> List[str]:
        """Generate 3 relevant follow-up questions from the query context."""
        # For now, return intelligent defaults; in a full LLM pass, this would be a separate prompt.
        return [
            f"What is the risk rating of {query}?",
            "How does this fund's return compare to its benchmark?",
            "What is the minimum investment for this fund?"
        ]

    def process_query(self, query: str) -> Tuple[str, Optional[str], List[str], bool]:
        """
        Main query pipeline:
        1. Scope guard
        2. Semantic search (Phase 2)
        3. LLM Answer generation
        4. Suggestion generation
        """
        # Scope Guard
        if not self.check_scope(query):
            return (
                "I am sorry, but I can only assist with mutual fund-specific details from INDmoney. I cannot provide general advice or off-topic information.",
                None,
                ["Tell me about Equity funds", "What is an NAV?", "How much should I invest in a SIP?"],
                False
            )

        # Retrieval (Phase 2)
        results = self.retriever.search(query, top_k=3)
        if not results:
             return ("I'm sorry, I don't have information on that specific fund detail.", None, [], True)

        context_texts = [r["text"] for r in results]
        source_url = results[0]["metadata"].get("source_url")

        # Answer Generation
        try:
            if self.client is None:
                answer = "[Mock LLM Response] Please add your GROQ_API_KEY to the .env file to generate real answers. Based on the retrieved context: " + context_texts[0][:150] + "..."
            else:
                prompt = self.get_grounding_prompt(query, context_texts)
                chat_completion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model_id,
                    temperature=0.1,  # Keep it grounded
                    max_tokens=300,
                )
                answer = chat_completion.choices[0].message.content.strip()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[ERROR] Groq API Error: {e}")
            answer = "I'm sorry, but I encountered an error while processing your request."

        # Suggestions
        suggestions = self.generate_suggestions(query, " ".join(context_texts))

        return answer, source_url, suggestions, True

def get_trending_suggestions() -> List[str]:
    """Fallback trending suggestions using the supported 10 funds."""
    return [
        "What is the 3Y return of Quant Small Cap Fund?",
        "What is the exit load for HDFC Infrastructure Fund?",
        "Who manages the LIC MF Gold ETF?"
    ]
