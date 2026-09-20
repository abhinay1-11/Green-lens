from app.services.identification.base import IdentificationProvider
from app.services.identification.factory import get_identification_provider
from app.services.identification.mock import MockProvider
from app.services.identification.plantnet import PlantNetProvider
from app.services.identification.bird import BirdProvider, LegacyBirdProvider
from app.services.identification.bioclip import BioCLIPBirdProvider
from app.services.identification.insect import InsectProvider
from app.services.identification.unknown_router import UnknownCategoryRouter

__all__ = [
    "IdentificationProvider",
    "get_identification_provider",
    "MockProvider",
    "PlantNetProvider",
    "BirdProvider",
    "BioCLIPBirdProvider",
    "LegacyBirdProvider",
    "InsectProvider",
    "UnknownCategoryRouter"
]
