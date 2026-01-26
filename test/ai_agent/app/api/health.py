"""Health check and system status endpoints."""

from fastapi import APIRouter

from app.core.config import settings
from app.db.base import engine
from app.memory.redis_memory import redis_memory
from app.schemas.chat import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Check the health of all services.

    Returns status of:
    - API server
    - PostgreSQL database
    - Redis cache
    """
    services = {}

    # Check PostgreSQL
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        services["postgresql"] = "healthy"
    except Exception as e:
        services["postgresql"] = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        if redis_memory.redis:
            await redis_memory.redis.ping()
            services["redis"] = "healthy"
        else:
            services["redis"] = "not connected"
    except Exception as e:
        services["redis"] = f"unhealthy: {str(e)}"

    # Overall status
    all_healthy = all(v == "healthy" for v in services.values())
    status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=status,
        version="1.0.0",
        services=services,
    )


@router.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
