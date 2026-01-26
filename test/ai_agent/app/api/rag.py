"""RAG API endpoints for document management and search."""

from typing import List

from fastapi import APIRouter, HTTPException

from app.rag.retriever import rag_manager
from app.schemas.chat import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    RAGSearchRequest,
    RAGSearchResponse,
    RAGSearchResult,
)

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_document(request: DocumentIngestRequest) -> DocumentIngestResponse:
    """
    Ingest a document into the RAG knowledge base.

    The document will be:
    1. Split into chunks
    2. Embedded using the configured embedding model
    3. Stored in Redis vector store for similarity search
    4. Persisted in PostgreSQL for long-term storage
    """
    try:
        embedding_ids = await rag_manager.ingest_document(
            content=request.content,
            title=request.title,
            source=request.source,
            doc_type=request.doc_type,
            metadata=request.metadata,
        )

        return DocumentIngestResponse(
            title=request.title,
            chunk_count=len(embedding_ids),
            embedding_ids=embedding_ids,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest document: {str(e)}",
        )


@router.post("/ingest/batch", response_model=List[DocumentIngestResponse])
async def ingest_documents_batch(
    documents: List[DocumentIngestRequest],
) -> List[DocumentIngestResponse]:
    """Ingest multiple documents in batch."""
    results = []

    for doc in documents:
        try:
            embedding_ids = await rag_manager.ingest_document(
                content=doc.content,
                title=doc.title,
                source=doc.source,
                doc_type=doc.doc_type,
                metadata=doc.metadata,
            )

            results.append(
                DocumentIngestResponse(
                    title=doc.title,
                    chunk_count=len(embedding_ids),
                    embedding_ids=embedding_ids,
                )
            )

        except Exception as e:
            results.append(
                DocumentIngestResponse(
                    title=doc.title,
                    chunk_count=0,
                    embedding_ids=[],
                )
            )

    return results


@router.post("/search", response_model=RAGSearchResponse)
async def search_documents(request: RAGSearchRequest) -> RAGSearchResponse:
    """
    Search for relevant documents using hybrid search.

    Combines vector similarity search with keyword matching for optimal results.
    """
    try:
        # Set retriever weights
        rag_manager.retriever.vector_weight = request.vector_weight
        rag_manager.retriever.keyword_weight = request.keyword_weight

        results = await rag_manager.retrieve_with_scores(
            query=request.query,
            k=request.k,
        )

        search_results = [
            RAGSearchResult(
                content=r["content"],
                score=r["score"],
                metadata=r["metadata"],
            )
            for r in results
        ]

        return RAGSearchResponse(
            query=request.query,
            results=search_results,
            count=len(search_results),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/search")
async def search_documents_get(
    query: str,
    k: int = 5,
    vector_weight: float = 0.7,
) -> RAGSearchResponse:
    """Search documents using GET request (simpler for testing)."""
    request = RAGSearchRequest(
        query=query,
        k=k,
        vector_weight=vector_weight,
        keyword_weight=1 - vector_weight,
    )
    return await search_documents(request)
