"""RAG (Retrieval Augmented Generation) service."""
from typing import List, Optional
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.services.vector_store import vector_store_manager
from app.config import settings


class RAGService:
    """Service for RAG operations."""

    def __init__(self):
        """Initialize RAG service."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks.

        Args:
            documents: List of documents to split

        Returns:
            List of chunked documents
        """
        return self.text_splitter.split_documents(documents)

    async def add_documents(
        self,
        documents: List[Document],
        subject: str
    ):
        """Add documents to the vector store.

        Args:
            documents: List of documents
            subject: Subject category (math, physics, chemistry)
        """
        # Split documents into chunks
        chunks = self.split_documents(documents)

        # Add subject metadata
        for chunk in chunks:
            chunk.metadata["subject"] = subject

        # Get vector store for subject
        store = vector_store_manager.get_store(subject)

        # Add documents to store
        await store.add_documents(chunks)

    async def retrieve(
        self,
        query: str,
        subject: Optional[str] = None,
        k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Document]:
        """Retrieve relevant documents.

        Args:
            query: Query text
            subject: Optional subject filter
            k: Number of documents to retrieve
            score_threshold: Minimum relevance score

        Returns:
            List of relevant documents
        """
        if subject:
            # Search in specific subject store
            store = vector_store_manager.get_store(subject)
            results = await store.similarity_search_with_score(query, k=k)
        else:
            # Search across all subjects
            all_results = []
            for subj in ["math", "physics", "chemistry"]:
                store = vector_store_manager.get_store(subj)
                results = await store.similarity_search_with_score(query, k=k)
                all_results.extend(results)

            # Sort by score and take top k
            all_results.sort(key=lambda x: x[1], reverse=True)
            results = all_results[:k]

        # Filter by score threshold
        filtered_results = [
            doc for doc, score in results
            if score >= score_threshold
        ]

        return filtered_results

    def format_context(self, documents: List[Document]) -> str:
        """Format retrieved documents into context string.

        Args:
            documents: List of documents

        Returns:
            Formatted context string
        """
        if not documents:
            return ""

        context_parts = []
        for i, doc in enumerate(documents, 1):
            subject = doc.metadata.get("subject", "unknown")
            topic = doc.metadata.get("topic", "")
            source = doc.metadata.get("source", "")

            context_parts.append(
                f"[文档 {i}] 学科: {subject}"
                + (f", 主题: {topic}" if topic else "")
                + (f", 来源: {source}" if source else "")
                + f"\n{doc.page_content}\n"
            )

        return "\n".join(context_parts)


# Global RAG service instance
rag_service = RAGService()
