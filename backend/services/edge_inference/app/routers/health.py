from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for Edge Inference service."""
    return {
        "service": "edge-inference",
        "status": "healthy",
        "version": "0.1.0"
    }
