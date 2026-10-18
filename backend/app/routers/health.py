from fastapi import APIRouter
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health():
    """Health check endpoint confirming the backend service status."""
    return HealthResponse(
        status="ok",
        app="SkillBridge"
    )
