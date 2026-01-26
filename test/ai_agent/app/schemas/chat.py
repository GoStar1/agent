"""Pydantic schemas for chat API."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="User ID")
    enable_rag: bool = Field(True, description="Enable RAG retrieval")
    stream: bool = Field(False, description="Enable streaming response")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""

    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session ID")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Tools used")
    iterations: int = Field(0, description="Number of agent iterations")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StreamEvent(BaseModel):
    """Schema for streaming events."""

    type: str = Field(..., description="Event type: token, tool_start, tool_end, done")
    content: Optional[str] = Field(None, description="Content for token events")
    tool: Optional[str] = Field(None, description="Tool name for tool events")
    output: Optional[str] = Field(None, description="Tool output")
    session_id: str = Field(..., description="Session ID")


class SessionCreateRequest(BaseModel):
    """Request to create a new session."""

    user_id: str = Field(..., description="User ID")
    initial_context: Optional[Dict[str, Any]] = Field(None, description="Initial context")


class SessionResponse(BaseModel):
    """Response for session operations."""

    session_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0


class DocumentIngestRequest(BaseModel):
    """Request to ingest documents into RAG."""

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source: Optional[str] = Field(None, max_length=500)
    doc_type: Optional[str] = Field(None, max_length=50)
    metadata: Optional[Dict[str, Any]] = Field(None)


class DocumentIngestResponse(BaseModel):
    """Response for document ingestion."""

    title: str
    chunk_count: int
    embedding_ids: List[str]


class RAGSearchRequest(BaseModel):
    """Request for RAG search."""

    query: str = Field(..., min_length=1, max_length=1000)
    k: int = Field(5, ge=1, le=20, description="Number of results")
    vector_weight: float = Field(0.7, ge=0, le=1)
    keyword_weight: float = Field(0.3, ge=0, le=1)


class RAGSearchResult(BaseModel):
    """Single search result."""

    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGSearchResponse(BaseModel):
    """Response for RAG search."""

    query: str
    results: List[RAGSearchResult]
    count: int


class UserCreate(BaseModel):
    """Request to create a user."""

    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=255)


class UserResponse(BaseModel):
    """User response schema."""

    id: uuid.UUID
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    services: Dict[str, str]
