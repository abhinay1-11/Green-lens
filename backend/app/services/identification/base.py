from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.schemas.identification import PredictionResponse

class IdentificationProvider(ABC):
    """
    Abstract Base Class for all species identification model adapters.
    """

    @abstractmethod
    def identify(
        self,
        images: List[Dict[str, Any]], # List of dicts with file_bytes, filename, organ
        category: str,
        location: Optional[Dict[str, float]] = None
    ) -> PredictionResponse:
        """
        Executes identification inference request and returns a normalized PredictionResponse object.
        """
        pass
