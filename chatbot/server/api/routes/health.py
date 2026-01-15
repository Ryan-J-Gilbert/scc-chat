"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "chatbot-api"
    }