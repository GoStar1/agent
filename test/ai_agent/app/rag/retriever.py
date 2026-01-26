"""RAG Retriever with Hybrid Search capabilities."""

import uuid
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import Field

from app.db.base import get_db_session
from app.db.crud import DocumentCRUD
from app.memory.vector_store import VectorDocument, vector_store


class HybridRetriever(BaseRetriever):
    """Custom retriever that combines vector and keyword search."""

    k: int = Field(default=5, description="Number of documents to retrieve")
    vector_weight: float = Field(
        default=0.7, description="Weight for vector search results"
    )
    keyword_weight: float = Field(
        default=0.3, description="Weight for keyword search results"
    )
    score_threshold: Optional[float] = Field(
        default=None, description="Minimum score threshold"
    )
    include_metadata: bool = Field(
        default=True, description="Include metadata in results"
    )

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(self, query: str) -> List[Document]:
        """Synchronous retrieval - not implemented for async-only store."""
        raise NotImplementedError("Use async retrieval with aget_relevant_documents")

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """Retrieve relevant documents using hybrid search."""
        results = await vector_store.hybrid_search(
            query=query,
            k=self.k,
            vector_weight=self.vector_weight,
            keyword_weight=self.keyword_weight,
            score_threshold=self.score_threshold,
        )

        documents = []
        for result in results:
            metadata = result.metadata.copy() if self.include_metadata else {}
            metadata["score"] = result.score
            metadata["doc_id"] = result.id

            doc = Document(
                page_content=result.content,
                metadata=metadata,
            )
            documents.append(doc)

        return documents


class RAGManager:
    """Manager for RAG operations including document ingestion and retrieval."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        k: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ):
        """Initialize RAG manager."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.retriever = HybridRetriever(
            k=k,
            vector_weight=vector_weight,
            keyword_weight=keyword_weight,
        )

    async def ingest_document(
        self,
        content: str,
        title: str,
        source: Optional[str] = None,
        doc_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Ingest a document by splitting and storing chunks."""
        # Split document into chunks
        chunks = self.text_splitter.split_text(content)

        if not chunks:
            return []

        parent_id = uuid.uuid4()
        embedding_ids = []
        db_documents = []

        async with get_db_session() as session:
            for i, chunk in enumerate(chunks):
                # Generate embedding ID
                embedding_id = await vector_store.add_document(
                    content=chunk,
                    metadata={
                        "title": title,
                        "source": source,
                        "doc_type": doc_type,
                        "chunk_index": i,
                        "parent_id": str(parent_id),
                        **(metadata or {}),
                    },
                    title=title,
                )
                embedding_ids.append(embedding_id)

                # Prepare DB document
                db_documents.append({
                    "title": title,
                    "content": chunk,
                    "source": source,
                    "doc_type": doc_type,
                    "chunk_index": i,
                    "parent_id": parent_id,
                    "embedding_id": embedding_id,
                    "metadata_": metadata or {},
                })

            # Store in PostgreSQL for persistence
            await DocumentCRUD.create_batch(session, db_documents)

        return embedding_ids

    async def ingest_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> Dict[str, List[str]]:
        """Ingest multiple documents."""
        results = {}
        for doc in documents:
            embedding_ids = await self.ingest_document(
                content=doc["content"],
                title=doc["title"],
                source=doc.get("source"),
                doc_type=doc.get("doc_type"),
                metadata=doc.get("metadata"),
            )
            results[doc["title"]] = embedding_ids
        return results

    async def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
    ) -> List[Document]:
        """Retrieve relevant documents for a query."""
        if k:
            self.retriever.k = k
        return await self.retriever.aget_relevant_documents(query)

    async def retrieve_with_scores(
        self,
        query: str,
        k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve documents with their relevance scores."""
        documents = await self.retrieve(query, k)
        return [
            {
                "content": doc.page_content,
                "score": doc.metadata.get("score", 0),
                "metadata": {
                    k: v for k, v in doc.metadata.items() if k != "score"
                },
            }
            for doc in documents
        ]

    async def delete_document(self, parent_id: uuid.UUID) -> int:
        """Delete a document and all its chunks."""
        async with get_db_session() as session:
            # Get all chunks
            documents = await session.execute(
                "SELECT embedding_id FROM documents WHERE parent_id = :parent_id",
                {"parent_id": parent_id},
            )

            # Delete from vector store
            for doc in documents:
                if doc.embedding_id:
                    await vector_store.delete_document(doc.embedding_id)

            # Delete from PostgreSQL
            deleted_count = await DocumentCRUD.delete_by_parent_id(session, parent_id)

        return deleted_count

    def format_context(self, documents: List[Document]) -> str:
        """Format retrieved documents into a context string."""
        if not documents:
            return "No relevant documents found."

        context_parts = []
        for i, doc in enumerate(documents, 1):
            score = doc.metadata.get("score", "N/A")
            source = doc.metadata.get("source", "Unknown")
            context_parts.append(
                f"[Document {i}] (Score: {score:.3f}, Source: {source})\n{doc.page_content}"
            )

        return "\n\n---\n\n".join(context_parts)


# Global instance
rag_manager = RAGManager()
