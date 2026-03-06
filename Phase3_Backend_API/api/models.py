from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user query about mutual funds.")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="The grounded AI answer (<=3 sentences).")
    source_url: Optional[str] = Field(None, description="The URL of the source material.")
    suggestions: List[str] = Field(..., description="3 AI-suggested follow-up questions.")
    is_in_scope: bool = Field(..., description="Whether the query was about mutual funds.")

class SuggestionResponse(BaseModel):
    suggestions: List[str] = Field(..., description="3 global trending questions.")

class SupportedFundsResponse(BaseModel):
    funds: List[str] = Field(..., description="List of recognized mutual fund names.")
