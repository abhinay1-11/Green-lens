import os
from typing import List, Optional, Dict, Any

from app.config import settings
from app.services.identification.base import IdentificationProvider
from app.services.identification.mock import MockProvider
from app.services.identification.bird_model import run_bird_species_classifier
from app.schemas.identification import PredictionResponse, PredictionItem, ErrorDetail
from app.utils.confidence import normalize_confidence


class LegacyBirdProvider(IdentificationProvider):
    """
    Lightweight Bird Species Identification Provider (ONNX CPU Classifier).
    Uses 525-species bird-specific ONNX model for high-accuracy local bird recognition.
    """

    def identify(
        self,
        images: List[Dict[str, Any]],
        category: str = "bird",
        location: Optional[Dict[str, float]] = None
    ) -> PredictionResponse:
        if not images:
            return PredictionResponse(
                success=False,
                category="bird",
                provider="bird_local_ai",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                error=ErrorDetail(code="INVALID_IMAGE", message="No valid bird image provided.")
            )

        raw_bytes = images[0].get("file_bytes")
        if not raw_bytes and images[0].get("saved_path") and os.path.exists(images[0]["saved_path"]):
            with open(images[0]["saved_path"], "rb") as f:
                raw_bytes = f.read()

        if not raw_bytes:
            return PredictionResponse(
                success=False,
                category="bird",
                provider="bird_local_ai",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                error=ErrorDetail(code="INVALID_IMAGE", message="No valid bird image provided.")
            )

        try:
            raw_predictions = run_bird_species_classifier(raw_bytes)

            predictions = []
            for idx, (sci_name, common_name, score) in enumerate(raw_predictions, start=1):
                norm_score = normalize_confidence(score)
                predictions.append(
                    PredictionItem(
                        rank=idx,
                        scientific_name=sci_name,
                        common_names=[common_name],
                        confidence=norm_score,
                        taxonomic_rank="species"
                    )
                )

            top_score = predictions[0].confidence if predictions else 0.0
            top2_score = predictions[1].confidence if len(predictions) > 1 else 0.0

            if top_score >= 0.70:
                ident_status = "HIGH_CONFIDENCE"
            elif len(predictions) > 1 and (top_score - top2_score) < 0.10 and top_score < 0.70:
                ident_status = "AMBIGUOUS"
            elif top_score >= 0.40:
                ident_status = "MEDIUM_CONFIDENCE"
            else:
                ident_status = "LOW_CONFIDENCE"

            return PredictionResponse(
                success=True,
                category="bird",
                detected_category="bird",
                provider="bird_local_ai",
                model_name="Bird Species ONNX Classifier",
                model_version="v1.0",
                identification_status=ident_status,
                predictions=predictions,
                is_mock=False
            )

        except Exception as exc:
            print(f"Bird ONNX classifier error: {exc}")
            return PredictionResponse(
                success=False,
                category="bird",
                provider="bird_local_ai",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                is_mock=False,
                error=ErrorDetail(
                    code="BIRD_PROVIDER_UNAVAILABLE",
                    message=f"Bird species classifier inference error: {str(exc)}"
                )
            )


class BirdProvider(IdentificationProvider):
    """
    Main Bird Identification Provider Router.
    Routes inference requests to Bird Species ONNX Classifier by default,
    or BioCLIPBirdProvider / MockProvider based on settings.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.legacy_provider = LegacyBirdProvider()
        self.mock_provider = MockProvider()

    def identify(
        self,
        images: List[Dict[str, Any]],
        category: str = "bird",
        location: Optional[Dict[str, float]] = None
    ) -> PredictionResponse:
        # Mock mode override
        if settings.IDENTIFICATION_MODE == "mock":
            res = self.mock_provider.identify(images, category="bird", location=location)
            res.detected_category = "bird"
            return res

        provider_choice = getattr(settings, "BIRD_IDENTIFICATION_PROVIDER", "local_onnx").lower()

        if provider_choice == "bioclip":
            print("[IDENTIFY] Category: bird")
            print("[IDENTIFY] Provider: BioCLIPBirdProvider")
            from app.services.identification.bioclip import BioCLIPBirdProvider
            return BioCLIPBirdProvider().identify(images, category=category, location=location)
        else:
            print("[IDENTIFY] Category: bird")
            print("[IDENTIFY] Provider: LegacyBirdProvider (ONNX)")
            return self.legacy_provider.identify(images, category=category, location=location)


