from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for Edge AI Gateway service."""
    return {
        "service": "edge-ai-gateway",
        "status": "healthy",
        "version": "0.1.0"
    }
