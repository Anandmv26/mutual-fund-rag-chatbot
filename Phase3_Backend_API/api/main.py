import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Relative imports to Phase 3 core and models
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "Phase2_Embedding_Retrieval", "search"))

from models import ChatRequest, ChatResponse, SuggestionResponse, SupportedFundsResponse  # noqa: E402
from core import Phase3Chatbot, get_trending_suggestions, SUPPORTED_FUNDS  # noqa: E402
from retriever import IMPORT_ERROR # noqa: E402

app = FastAPI(
    title="Mutual Fund RAG Chatbot API",
    description="Backend for the Mutual Fund RAG Chatbot Phase 3.",
    version="1.0.0"
)

# CORS configuration for Phase 4 Frontend (React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared chatbot instance
chatbot = Phase3Chatbot()

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handles user queries and returns a grounded response."""
    try:
        answer, source_url, suggestions, is_in_scope = chatbot.process_query(request.message)
        return ChatResponse(
            answer=answer,
            source_url=source_url,
            suggestions=suggestions,
            is_in_scope=is_in_scope
        )
    except Exception as e:
        print(f"[ERROR] Chat Endpoint Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/suggestions", response_model=SuggestionResponse)
async def suggestions_endpoint():
    """Returns global trending suggestions for initial load."""
    return SuggestionResponse(suggestions=get_trending_suggestions())

@app.get("/supported-funds", response_model=SupportedFundsResponse)
async def supported_funds_endpoint():
    """Returns the list of 10 supported mutual funds."""
    return SupportedFundsResponse(funds=SUPPORTED_FUNDS)

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "Mutual Fund RAG Chatbot"}

@app.get("/health/debug")
async def health_debug():
    """Debug info on data loading."""
    retriever = chatbot.retriever
    return {
        "status": "online",
        "fund_count": retriever.count,
        "import_error": IMPORT_ERROR,
        "has_model": retriever.model is not None,
        "has_embeddings": retriever.embeddings is not None,
        "data_dir": retriever.raw_data_dir,
        "abs_data_dir": os.path.abspath(retriever.raw_data_dir),
        "dir_exists": os.path.exists(retriever.raw_data_dir)
    }
