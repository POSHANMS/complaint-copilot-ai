from fastapi import APIRouter
from app.db.schemas import HealthResponse
from app.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        service=settings.PROJECT_NAME
    )
