
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health", tags=["Health"])
def health_check():
    """Readiness/Liveness endpoint for health checking."""
    return {"status": "OK", "timestamp": datetime.utcnow()}
