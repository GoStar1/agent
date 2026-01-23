"""Pydantic schemas for chat API."""
from pydantic import BaseModel
from typing import List, Optional


class ChatMessage(BaseModel):
    """Chat message schema."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Chat request schema."""
    message: str
    user_id: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response schema."""
    response: str
    conversation_id: str
    sources: Optional[List[dict]] = None
