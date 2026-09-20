from app.config import settings
from app.services.identification.base import IdentificationProvider
from app.services.identification.mock import MockProvider
from app.services.identification.plantnet import PlantNetProvider
from app.services.identification.bird import BirdProvider
from app.services.identification.insect import InsectProvider
from app.services.identification.unknown_router import UnknownCategoryRouter

def get_identification_provider(category: str) -> IdentificationProvider:
    """
    Factory function selecting appropriate specialized identification provider based on category and config.
    """
    cat = (category or "").lower()

    # Explicit mock mode override (development only)
    if settings.IDENTIFICATION_MODE == "mock":
        return MockProvider()

    # Real identification mode routing
    if cat == "plant":
        return PlantNetProvider()

    elif cat == "bird":
        return BirdProvider()

    elif cat == "insect":
        return InsectProvider()

    elif cat == "unknown":
        return UnknownCategoryRouter()

    else:
        return UnknownCategoryRouter()
