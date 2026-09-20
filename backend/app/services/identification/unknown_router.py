from typing import List, Optional, Dict, Any

from app.config import settings
from app.services.identification.base import IdentificationProvider
from app.services.identification.mock import MockProvider
from app.services.identification.plantnet import PlantNetProvider
from app.services.identification.bird import BirdProvider
from app.services.identification.insect import InsectProvider
from app.schemas.identification import PredictionResponse, ErrorDetail

class UnknownCategoryRouter(IdentificationProvider):
    """
    Automated Category Detector & Classifier for 'unknown' organism category.
    Performs Stage-1 category evaluation across Plant, Bird, and Insect classifiers to find the best species match.
    Sets detected_category in response.
    """

    def __init__(self):
        self.plant_provider = PlantNetProvider()
        self.bird_provider = BirdProvider()
        self.insect_provider = InsectProvider()
        self.mock_fallback = MockProvider()

    def identify(
        self,
        images: List[Dict[str, Any]],
        category: str = "unknown",
        location: Optional[Dict[str, float]] = None
    ) -> PredictionResponse:
        if settings.IDENTIFICATION_MODE == "mock":
            res = self.mock_fallback.identify(images, category="plant", location=location)
            res.detected_category = "plant"
            return res

        if not images or not images[0].get("file_bytes"):
            return PredictionResponse(
                success=False,
                category="unknown",
                detected_category="unknown",
                provider="category_detector",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                error=ErrorDetail(code="INVALID_IMAGE", message="No image provided for category detection.")
            )

        # Run inference across Plant, Bird, and Insect providers
        plant_res = self.plant_provider.identify(images, category="plant", location=location)
        bird_res = self.bird_provider.identify(images, category="bird", location=location)
        insect_res = self.insect_provider.identify(images, category="insect", location=location)

        candidates = []
        if plant_res.success and plant_res.predictions:
            candidates.append((plant_res.predictions[0].confidence, "plant", plant_res))
        if bird_res.success and bird_res.predictions:
            candidates.append((bird_res.predictions[0].confidence, "bird", bird_res))
        if insect_res.success and insect_res.predictions:
            candidates.append((insect_res.predictions[0].confidence, "insect", insect_res))

        if candidates:
            # Sort by top prediction confidence
            candidates.sort(key=lambda x: x[0], reverse=True)
            top_score, top_cat, best_res = candidates[0]

            if top_score >= 0.20:
                best_res.detected_category = top_cat
                return best_res

        return PredictionResponse(
            success=False,
            category="unknown",
            detected_category="unknown",
            provider="category_detector",
            identification_status="UNABLE_TO_DETERMINE_CATEGORY",
            predictions=[],
            error=ErrorDetail(
                code="CATEGORY_UNDETERMINED",
                message="Could not determine organism category with high confidence. Please manually select Plant, Bird, or Insect."
            )
        )
