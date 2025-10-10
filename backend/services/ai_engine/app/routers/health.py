from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for AI Engine service."""
    return {
        "service": "ai-engine",
        "status": "healthy",
        "version": "0.1.0"
    }
