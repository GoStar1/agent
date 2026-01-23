"""FAISS vector store implementation."""
import os
import pickle
from typing import List, Dict, Optional, Tuple
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from app.core.embeddings import embedding_service
from app.config import settings


class VectorStore:
    """FAISS vector store for document retrieval."""

    def __init__(self, subject: str = "general"):
        """Initialize vector store for a specific subject.

        Args:
            subject: Subject name (math, physics, chemistry, or general)
        """
        self.subject = subject
        self.store_path = os.path.join(settings.vector_store_path, subject)
        self.vector_store: Optional[FAISS] = None
        self._load_or_create()

    def _load_or_create(self):
        """Load existing vector store or create a new one."""
        if os.path.exists(self.store_path):
            try:
                self.vector_store = FAISS.load_local(
                    self.store_path,
                    embedding_service.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Error loading vector store: {e}")
                self.vector_store = None
        else:
            self.vector_store = None

    async def add_documents(self, documents: List[Document]):
        """Add documents to the vector store.

        Args:
            documents: List of Document objects
        """
        if self.vector_store is None:
            # Create new vector store
            self.vector_store = await FAISS.afrom_documents(
                documents,
                embedding_service.embeddings
            )
        else:
            # Add to existing vector store
            await self.vector_store.aadd_documents(documents)

        # Save to disk
        self.save()

    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None
    ) -> List[Document]:
        """Search for similar documents.

        Args:
            query: Query text
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of similar documents
        """
        if self.vector_store is None:
            return []

        results = await self.vector_store.asimilarity_search(
            query,
            k=k,
            filter=filter
        )
        return results

    async def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """Search for similar documents with relevance scores.

        Args:
            query: Query text
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of (document, score) tuples
        """
        if self.vector_store is None:
            return []

        results = await self.vector_store.asimilarity_search_with_score(
            query,
            k=k,
            filter=filter
        )
        return results

    def save(self):
        """Save vector store to disk."""
        if self.vector_store is not None:
            os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
            self.vector_store.save_local(self.store_path)

    def delete(self):
        """Delete vector store from disk."""
        if os.path.exists(self.store_path):
            import shutil
            shutil.rmtree(self.store_path)
        self.vector_store = None


class VectorStoreManager:
    """Manager for multiple subject-specific vector stores."""

    def __init__(self):
        """Initialize vector store manager."""
        self.stores: Dict[str, VectorStore] = {}

    def get_store(self, subject: str) -> VectorStore:
        """Get or create a vector store for a subject.

        Args:
            subject: Subject name

        Returns:
            VectorStore instance
        """
        if subject not in self.stores:
            self.stores[subject] = VectorStore(subject)
        return self.stores[subject]

    async def search_all(
        self,
        query: str,
        k: int = 5
    ) -> Dict[str, List[Document]]:
        """Search across all subject stores.

        Args:
            query: Query text
            k: Number of results per subject

        Returns:
            Dictionary mapping subject to results
        """
        results = {}
        for subject, store in self.stores.items():
            results[subject] = await store.similarity_search(query, k=k)
        return results


# Global vector store manager
vector_store_manager = VectorStoreManager()
