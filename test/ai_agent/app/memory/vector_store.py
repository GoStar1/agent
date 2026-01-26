"""Redis Vector Store for embedding storage and similarity search."""

import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import redis.asyncio as redis
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel

from app.core.config import settings


class VectorDocument(BaseModel):
    """Document with vector embedding."""

    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}
    score: Optional[float] = None


class RedisVectorStore:
    """Redis-based vector store for semantic search."""

    def __init__(self, index_name: str = "documents"):
        """Initialize Redis vector store."""
        self.redis: Optional[redis.Redis] = None
        self.index_name = index_name
        self.embedding_dim = settings.embedding_dimension
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )

    async def connect(self) -> None:
        """Establish Redis connection and create index."""
        self.redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        await self.redis.ping()
        await self._create_index()

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

    async def _create_index(self) -> None:
        """Create Redis Search index for vector similarity."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        try:
            # Check if index exists
            await self.redis.execute_command("FT.INFO", self.index_name)
        except redis.ResponseError:
            # Create the index
            schema = f"""
                ON HASH PREFIX 1 doc:
                SCHEMA
                    content TEXT WEIGHT 1.0
                    title TEXT WEIGHT 2.0
                    metadata TEXT
                    embedding VECTOR FLAT 6
                        TYPE FLOAT32
                        DIM {self.embedding_dim}
                        DISTANCE_METRIC COSINE
            """
            await self.redis.execute_command(
                "FT.CREATE",
                self.index_name,
                *schema.split(),
            )

    def _generate_doc_id(self, content: str) -> str:
        """Generate a unique document ID based on content hash."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"{uuid.uuid4().hex[:8]}_{content_hash}"

    async def add_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> str:
        """Add a single document to the vector store."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        doc_id = doc_id or self._generate_doc_id(content)
        key = f"doc:{doc_id}"

        # Generate embedding
        embedding = await self.embeddings.aembed_query(content)
        embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()

        # Store document
        await self.redis.hset(
            key,
            mapping={
                "content": content,
                "title": title or "",
                "metadata": json.dumps(metadata or {}),
                "embedding": embedding_bytes,
            },
        )

        return doc_id

    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[str]:
        """Add multiple documents to the vector store."""
        doc_ids = []
        for doc in documents:
            doc_id = await self.add_document(
                content=doc["content"],
                metadata=doc.get("metadata"),
                doc_id=doc.get("id"),
                title=doc.get("title"),
            )
            doc_ids.append(doc_id)
        return doc_ids

    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        score_threshold: Optional[float] = None,
    ) -> List[VectorDocument]:
        """Perform vector similarity search."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        # Generate query embedding
        query_embedding = await self.embeddings.aembed_query(query)
        query_vector = np.array(query_embedding, dtype=np.float32).tobytes()

        # Build search query
        search_query = f"*=>[KNN {k} @embedding $vector AS score]"

        # Execute search
        results = await self.redis.execute_command(
            "FT.SEARCH",
            self.index_name,
            search_query,
            "PARAMS",
            "2",
            "vector",
            query_vector,
            "SORTBY",
            "score",
            "LIMIT",
            "0",
            str(k),
            "RETURN",
            "4",
            "content",
            "title",
            "metadata",
            "score",
            "DIALECT",
            "2",
        )

        return self._parse_search_results(results, score_threshold)

    async def keyword_search(
        self,
        query: str,
        k: int = 5,
    ) -> List[VectorDocument]:
        """Perform keyword-based full-text search."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        # Escape special characters
        escaped_query = self._escape_query(query)

        # Execute search
        results = await self.redis.execute_command(
            "FT.SEARCH",
            self.index_name,
            escaped_query,
            "LIMIT",
            "0",
            str(k),
            "RETURN",
            "3",
            "content",
            "title",
            "metadata",
        )

        return self._parse_search_results(results)

    async def hybrid_search(
        self,
        query: str,
        k: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        score_threshold: Optional[float] = None,
    ) -> List[VectorDocument]:
        """Perform hybrid search combining vector and keyword search."""
        # Execute both searches
        vector_results = await self.similarity_search(query, k=k * 2)
        keyword_results = await self.keyword_search(query, k=k * 2)

        # Combine and rerank results
        combined_scores: Dict[str, Tuple[VectorDocument, float]] = {}

        # Add vector search results with weight
        for doc in vector_results:
            # Convert cosine distance to similarity (lower is better in Redis)
            similarity = 1 - (doc.score or 0)
            weighted_score = similarity * vector_weight
            combined_scores[doc.id] = (doc, weighted_score)

        # Add keyword search results with weight
        for doc in keyword_results:
            if doc.id in combined_scores:
                existing_doc, existing_score = combined_scores[doc.id]
                combined_scores[doc.id] = (existing_doc, existing_score + keyword_weight)
            else:
                combined_scores[doc.id] = (doc, keyword_weight)

        # Sort by combined score
        sorted_results = sorted(
            combined_scores.values(),
            key=lambda x: x[1],
            reverse=True,
        )

        # Apply threshold and limit
        final_results = []
        for doc, score in sorted_results[:k]:
            if score_threshold and score < score_threshold:
                continue
            doc.score = score
            final_results.append(doc)

        return final_results

    def _parse_search_results(
        self,
        results: Any,
        score_threshold: Optional[float] = None,
    ) -> List[VectorDocument]:
        """Parse Redis search results into VectorDocument objects."""
        if not results or results[0] == 0:
            return []

        documents = []
        # Results format: [count, key1, [field1, value1, ...], key2, ...]
        i = 1
        while i < len(results):
            key = results[i]
            doc_id = key.replace("doc:", "")
            fields = results[i + 1] if i + 1 < len(results) else []

            # Parse fields
            field_dict = {}
            for j in range(0, len(fields), 2):
                if j + 1 < len(fields):
                    field_dict[fields[j]] = fields[j + 1]

            score = float(field_dict.get("score", 0))
            if score_threshold and score > score_threshold:
                i += 2
                continue

            metadata = {}
            if "metadata" in field_dict:
                try:
                    metadata = json.loads(field_dict["metadata"])
                except json.JSONDecodeError:
                    pass

            doc = VectorDocument(
                id=doc_id,
                content=field_dict.get("content", ""),
                metadata=metadata,
                score=score,
            )
            documents.append(doc)
            i += 2

        return documents

    def _escape_query(self, query: str) -> str:
        """Escape special characters in Redis query."""
        special_chars = ["@", "!", "{", "}", "(", ")", "|", "-", "=", ">", "[", "]", ":", ";"]
        escaped = query
        for char in special_chars:
            escaped = escaped.replace(char, f"\\{char}")
        return escaped

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the vector store."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        result = await self.redis.delete(f"doc:{doc_id}")
        return result > 0

    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Retrieve a specific document by ID."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        data = await self.redis.hgetall(f"doc:{doc_id}")
        if not data:
            return None

        metadata = {}
        if "metadata" in data:
            try:
                metadata = json.loads(data["metadata"])
            except json.JSONDecodeError:
                pass

        return VectorDocument(
            id=doc_id,
            content=data.get("content", ""),
            metadata=metadata,
        )


# Global instance
vector_store = RedisVectorStore()
