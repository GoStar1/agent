"""Embedding service for document vectorization."""
from langchain_openai import OpenAIEmbeddings
from app.config import settings
from typing import List


class EmbeddingService:
    """Service for generating embeddings."""

    def __init__(self):
        """Initialize embedding service."""
        # Use ModelScope API for embeddings
        api_key = settings.embedding_api_key or settings.llm_api_key
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=api_key,
            openai_api_base=settings.embedding_base_url,
        )

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents.

        Args:
            texts: List of text documents

        Returns:
            List of embedding vectors
        """
        return await self.embeddings.aembed_documents(texts)

    async def embed_query(self, text: str) -> List[float]:
        """Embed a single query.

        Args:
            text: Query text

        Returns:
            Embedding vector
        """
        return await self.embeddings.aembed_query(text)


# Global embedding service instance
embedding_service = EmbeddingService()
