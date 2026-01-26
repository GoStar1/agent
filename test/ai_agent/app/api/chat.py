"""Chat API endpoints with streaming support."""

import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.agent.react_agent import ReActAgent
from app.memory.redis_memory import redis_memory
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SessionCreateRequest,
    SessionResponse,
    StreamEvent,
)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the AI agent and get a response.

    - **message**: The user's message
    - **session_id**: Optional session ID for conversation continuity
    - **enable_rag**: Enable RAG-based context retrieval
    - **stream**: If true, use the /chat/stream endpoint instead
    """
    if request.stream:
        raise HTTPException(
            status_code=400,
            detail="For streaming responses, use the /chat/stream endpoint",
        )

    agent = ReActAgent(enable_rag=request.enable_rag)

    try:
        result = await agent.run(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id,
            metadata=request.metadata,
        )

        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            tool_calls=result.get("tool_calls", []),
            iterations=result.get("iterations", 0),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.post("/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """
    Stream chat responses from the AI agent.

    Returns Server-Sent Events (SSE) with the following event types:
    - token: A chunk of the response text
    - tool_start: Tool execution started
    - tool_end: Tool execution completed
    - done: Stream complete
    """
    agent = ReActAgent(enable_rag=request.enable_rag)

    async def generate_events() -> AsyncGenerator[str, None]:
        try:
            async for event in agent.stream(
                message=request.message,
                session_id=request.session_id,
                user_id=request.user_id,
                metadata=request.metadata,
            ):
                # Format as SSE
                event_data = StreamEvent(**event)
                yield f"data: {event_data.model_dump_json()}\n\n"

        except Exception as e:
            error_event = {
                "type": "error",
                "content": str(e),
                "session_id": request.session_id or "",
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest) -> SessionResponse:
    """Create a new chat session."""
    try:
        session_id = await redis_memory.create_session(
            user_id=request.user_id,
            initial_context=request.initial_context,
        )

        return SessionResponse(
            session_id=session_id,
            user_id=request.user_id,
            message_count=0,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """Get session information."""
    session = await redis_memory.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        message_count=len(session.messages),
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete a chat session."""
    deleted = await redis_memory.clear_session(session_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "deleted", "session_id": session_id}


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, limit: int = 50) -> dict:
    """Get messages from a session."""
    session = await redis_memory.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = [
        {
            "role": msg.get("type", "unknown").replace("Message", "").lower(),
            "content": msg.get("content", ""),
            "timestamp": msg.get("timestamp"),
        }
        for msg in session.messages[-limit:]
    ]

    return {
        "session_id": session_id,
        "messages": messages,
        "count": len(messages),
    }
