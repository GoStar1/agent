"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, health, rag
from app.core.config import settings
from app.db.base import close_db, init_db
from app.memory.redis_memory import redis_memory
from app.memory.vector_store import vector_store


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown."""
    # Startup
    print(f"Starting {settings.app_name}...")

    # Initialize database
    try:
        await init_db()
        print("PostgreSQL connected and tables created")
    except Exception as e:
        print(f"Failed to initialize database: {e}")

    # Connect to Redis
    try:
        await redis_memory.connect()
        print("Redis memory connected")
    except Exception as e:
        print(f"Failed to connect Redis memory: {e}")

    # Connect vector store
    try:
        await vector_store.connect()
        print("Redis vector store connected")
    except Exception as e:
        print(f"Failed to connect vector store: {e}")

    # Set LangSmith environment variables
    if settings.langchain_tracing_v2:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        print(f"LangSmith tracing enabled for project: {settings.langchain_project}")

    print(f"{settings.app_name} started successfully!")

    yield

    # Shutdown
    print(f"Shutting down {settings.app_name}...")

    await redis_memory.disconnect()
    await vector_store.disconnect()
    await close_db()

    print("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Production-grade AI Agent with RAG, Multi-level Memory, and Tool Use",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(rag.router, prefix="/api/v1")

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        workers=1 if settings.debug else 4,
    )
