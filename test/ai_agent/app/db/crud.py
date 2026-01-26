"""CRUD operations for database models."""

import uuid
from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation, Document, Message, User


class UserCRUD:
    """CRUD operations for User model."""

    @staticmethod
    async def create(
        session: AsyncSession,
        username: str,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None,
    ) -> User:
        """Create a new user."""
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
        )
        session.add(user)
        await session.flush()
        return user

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(
        session: AsyncSession, username: str
    ) -> Optional[User]:
        """Get user by username."""
        result = await session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()


class ConversationCRUD:
    """CRUD operations for Conversation model."""

    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: uuid.UUID,
        title: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            user_id=user_id,
            title=title,
            metadata_=metadata or {},
        )
        session.add(conversation)
        await session.flush()
        return conversation

    @staticmethod
    async def get_by_id(
        session: AsyncSession, conversation_id: uuid.UUID
    ) -> Optional[Conversation]:
        """Get conversation by ID."""
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_conversations(
        session: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Conversation]:
        """Get user's conversations with pagination."""
        result = await session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.is_active == True)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def update_summary(
        session: AsyncSession,
        conversation_id: uuid.UUID,
        summary: str,
    ) -> Optional[Conversation]:
        """Update conversation summary."""
        conversation = await ConversationCRUD.get_by_id(session, conversation_id)
        if conversation:
            conversation.summary = summary
            await session.flush()
        return conversation


class MessageCRUD:
    """CRUD operations for Message model."""

    @staticmethod
    async def create(
        session: AsyncSession,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        token_count: Optional[int] = None,
        tool_calls: Optional[dict] = None,
        tool_call_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Message:
        """Create a new message."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            token_count=token_count,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            metadata_=metadata or {},
        )
        session.add(message)
        await session.flush()
        return message

    @staticmethod
    async def get_conversation_messages(
        session: AsyncSession,
        conversation_id: uuid.UUID,
        limit: int = 50,
        before: Optional[datetime] = None,
    ) -> Sequence[Message]:
        """Get messages for a conversation."""
        query = select(Message).where(Message.conversation_id == conversation_id)

        if before:
            query = query.where(Message.created_at < before)

        result = await session.execute(
            query.order_by(desc(Message.created_at)).limit(limit)
        )
        messages = result.scalars().all()
        return list(reversed(messages))

    @staticmethod
    async def count_conversation_messages(
        session: AsyncSession, conversation_id: uuid.UUID
    ) -> int:
        """Count messages in a conversation."""
        from sqlalchemy import func

        result = await session.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id
            )
        )
        return result.scalar() or 0


class DocumentCRUD:
    """CRUD operations for Document model."""

    @staticmethod
    async def create(
        session: AsyncSession,
        title: str,
        content: str,
        source: Optional[str] = None,
        doc_type: Optional[str] = None,
        chunk_index: int = 0,
        parent_id: Optional[uuid.UUID] = None,
        embedding_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Document:
        """Create a new document."""
        document = Document(
            title=title,
            content=content,
            source=source,
            doc_type=doc_type,
            chunk_index=chunk_index,
            parent_id=parent_id,
            embedding_id=embedding_id,
            metadata_=metadata or {},
        )
        session.add(document)
        await session.flush()
        return document

    @staticmethod
    async def create_batch(
        session: AsyncSession, documents: List[dict]
    ) -> List[Document]:
        """Create multiple documents."""
        db_documents = [Document(**doc) for doc in documents]
        session.add_all(db_documents)
        await session.flush()
        return db_documents

    @staticmethod
    async def get_by_id(
        session: AsyncSession, document_id: uuid.UUID
    ) -> Optional[Document]:
        """Get document by ID."""
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_embedding_ids(
        session: AsyncSession, embedding_ids: List[str]
    ) -> Sequence[Document]:
        """Get documents by embedding IDs."""
        result = await session.execute(
            select(Document).where(Document.embedding_id.in_(embedding_ids))
        )
        return result.scalars().all()

    @staticmethod
    async def search_by_keyword(
        session: AsyncSession,
        keyword: str,
        doc_type: Optional[str] = None,
        limit: int = 10,
    ) -> Sequence[Document]:
        """Search documents by keyword (simple LIKE search)."""
        query = select(Document).where(
            Document.content.ilike(f"%{keyword}%")
            | Document.title.ilike(f"%{keyword}%")
        )

        if doc_type:
            query = query.where(Document.doc_type == doc_type)

        result = await session.execute(query.limit(limit))
        return result.scalars().all()

    @staticmethod
    async def delete_by_parent_id(
        session: AsyncSession, parent_id: uuid.UUID
    ) -> int:
        """Delete all document chunks by parent ID."""
        from sqlalchemy import delete

        result = await session.execute(
            delete(Document).where(Document.parent_id == parent_id)
        )
        await session.flush()
        return result.rowcount
