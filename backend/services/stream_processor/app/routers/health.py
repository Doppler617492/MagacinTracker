from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for Stream Processor service."""
    return {
        "service": "stream-processor",
        "status": "healthy",
        "version": "0.1.0"
    }
