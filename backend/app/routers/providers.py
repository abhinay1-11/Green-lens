from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/providers", tags=["Providers"])

@router.get("/status")
def get_provider_status():
    """
    Returns configured identification model adapters and their configuration status.
    Never exposes API key secrets.
    """
    has_plantnet_key = bool(settings.clean_plantnet_api_key)
    is_real_mode = (settings.IDENTIFICATION_MODE == "real")
    bird_provider_choice = getattr(settings, "BIRD_IDENTIFICATION_PROVIDER", "bioclip").lower()

    return {
        "mode": settings.IDENTIFICATION_MODE,
        "plant": {
            "provider": "plantnet" if is_real_mode else "mock",
            "configured": has_plantnet_key,
            "available": True if is_real_mode else True,
            "fallback_available": True,
            "display_label": "Pl@ntNet API + Fallback Engine" if (has_plantnet_key and is_real_mode) else ("Biodiversity Fallback Engine" if is_real_mode else "Mock Engine")
        },
        "bird": {
            "provider": "BioCLIP 2" if is_real_mode else "mock",
            "configured": True,
            "available": True,
            "fallback_available": True,
            "display_label": "BioCLIP 2 Avian Engine" if is_real_mode else "Mock Engine"
        },
        "insect": {
            "provider": "insect_vision_ai" if is_real_mode else "mock",
            "configured": True,
            "available": True,
            "fallback_available": True,
            "display_label": "Insecta Vision AI Engine" if is_real_mode else "Mock Engine"
        },
        "biodiversity_fallback": {
            "provider": "inaturalist_biodiversity_vision" if is_real_mode else "mock",
            "configured": True,
            "available": True,
            "display_label": "General Biodiversity Vision Classifier" if is_real_mode else "Mock Engine"
        }
    }
