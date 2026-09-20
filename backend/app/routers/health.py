from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/")
@router.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "providers": {
            "plant": settings.PLANT_IDENTIFICATION_PROVIDER,
            "bird": settings.BIRD_IDENTIFICATION_PROVIDER,
            "insect": settings.INSECT_IDENTIFICATION_PROVIDER
        }
    }

