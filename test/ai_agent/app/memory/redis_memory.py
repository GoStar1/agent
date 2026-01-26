"""Redis-based memory management for short-term session storage."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from pydantic import BaseModel

from app.core.config import settings


class ConversationMemory(BaseModel):
    """In-memory conversation state."""

    session_id: str
    user_id: str
    messages: List[Dict[str, Any]] = []
    context: Dict[str, Any] = {}
    created_at: str = ""
    updated_at: str = ""


class RedisMemoryManager:
    """Manager for short-term memory storage in Redis."""

    def __init__(self):
        """Initialize Redis connection."""
        self.redis: Optional[redis.Redis] = None
        self.ttl = settings.short_term_memory_ttl
        self.max_history = settings.max_conversation_history

    async def connect(self) -> None:
        """Establish Redis connection."""
        self.redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        await self.redis.ping()

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

    def _session_key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"session:{session_id}"

    def _message_to_dict(self, message: BaseMessage) -> Dict[str, Any]:
        """Convert LangChain message to dictionary."""
        msg_dict = {
            "type": message.__class__.__name__,
            "content": message.content,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if hasattr(message, "tool_calls") and message.tool_calls:
            msg_dict["tool_calls"] = message.tool_calls

        if hasattr(message, "tool_call_id") and message.tool_call_id:
            msg_dict["tool_call_id"] = message.tool_call_id

        if message.additional_kwargs:
            msg_dict["additional_kwargs"] = message.additional_kwargs

        return msg_dict

    def _dict_to_message(self, msg_dict: Dict[str, Any]) -> BaseMessage:
        """Convert dictionary back to LangChain message."""
        msg_type = msg_dict.get("type", "HumanMessage")
        content = msg_dict.get("content", "")
        additional_kwargs = msg_dict.get("additional_kwargs", {})

        if msg_type == "HumanMessage":
            return HumanMessage(content=content, additional_kwargs=additional_kwargs)
        elif msg_type == "AIMessage":
            tool_calls = msg_dict.get("tool_calls", [])
            return AIMessage(
                content=content,
                additional_kwargs=additional_kwargs,
                tool_calls=tool_calls,
            )
        elif msg_type == "SystemMessage":
            return SystemMessage(content=content, additional_kwargs=additional_kwargs)
        elif msg_type == "ToolMessage":
            return ToolMessage(
                content=content,
                tool_call_id=msg_dict.get("tool_call_id", ""),
                additional_kwargs=additional_kwargs,
            )
        else:
            return HumanMessage(content=content)

    async def create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new conversation session."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        session_id = session_id or str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        memory = ConversationMemory(
            session_id=session_id,
            user_id=user_id,
            messages=[],
            context=initial_context or {},
            created_at=now,
            updated_at=now,
        )

        await self.redis.setex(
            self._session_key(session_id),
            self.ttl,
            memory.model_dump_json(),
        )

        return session_id

    async def get_session(self, session_id: str) -> Optional[ConversationMemory]:
        """Retrieve session from Redis."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        data = await self.redis.get(self._session_key(session_id))
        if data:
            return ConversationMemory.model_validate_json(data)
        return None

    async def add_message(
        self,
        session_id: str,
        message: BaseMessage,
    ) -> None:
        """Add a message to the session."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        msg_dict = self._message_to_dict(message)
        session.messages.append(msg_dict)

        # Trim to max history
        if len(session.messages) > self.max_history:
            session.messages = session.messages[-self.max_history :]

        session.updated_at = datetime.utcnow().isoformat()

        await self.redis.setex(
            self._session_key(session_id),
            self.ttl,
            session.model_dump_json(),
        )

    async def add_messages(
        self,
        session_id: str,
        messages: List[BaseMessage],
    ) -> None:
        """Add multiple messages to the session."""
        for message in messages:
            await self.add_message(session_id, message)

    async def get_messages(self, session_id: str) -> List[BaseMessage]:
        """Get all messages from session as LangChain messages."""
        session = await self.get_session(session_id)
        if not session:
            return []

        return [self._dict_to_message(msg) for msg in session.messages]

    async def get_recent_messages(
        self, session_id: str, limit: int = 10
    ) -> List[BaseMessage]:
        """Get recent messages from session."""
        messages = await self.get_messages(session_id)
        return messages[-limit:]

    async def update_context(
        self,
        session_id: str,
        context: Dict[str, Any],
        merge: bool = True,
    ) -> None:
        """Update session context."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if merge:
            session.context.update(context)
        else:
            session.context = context

        session.updated_at = datetime.utcnow().isoformat()

        await self.redis.setex(
            self._session_key(session_id),
            self.ttl,
            session.model_dump_json(),
        )

    async def clear_session(self, session_id: str) -> bool:
        """Clear a session from Redis."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        result = await self.redis.delete(self._session_key(session_id))
        return result > 0

    async def extend_session_ttl(self, session_id: str) -> bool:
        """Extend the TTL of a session."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        return await self.redis.expire(self._session_key(session_id), self.ttl)

    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        return await self.redis.exists(self._session_key(session_id)) > 0


# Global instance
redis_memory = RedisMemoryManager()
