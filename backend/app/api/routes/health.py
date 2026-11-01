from fastapi import APIRouter
from pydantic import BaseModel
from app.config import get_settings

router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    """Schema for health-check endpoint response."""
    name: str
    status: str
    message: str
    environment: str
    version: str


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """
    Health check endpoint returning the status of the SkillProof AI backend.
    """
    return HealthResponse(
        name=settings.app_name,
        status="ok",
        message="SkillProof AI Backend Service is running and healthy.",
        environment=settings.app_env,
        version=settings.version,
    )
