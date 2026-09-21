import os
from typing import List, Optional, Dict, Any

from app.config import settings
from app.services.identification.base import IdentificationProvider
from app.services.identification.mock import MockProvider
from app.services.identification.local_model import run_local_species_classifier
from app.schemas.identification import PredictionResponse, PredictionItem, ErrorDetail
from app.utils.confidence import normalize_confidence


class LegacyBirdProvider(IdentificationProvider):
    """
    Legacy Bird Species Identification Provider (PyTorch local classifier fallback).
    Preserved behind configuration flag for legacy system compatibility.
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
                provider="legacy_bird_ai",
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
                provider="legacy_bird_ai",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                error=ErrorDetail(code="INVALID_IMAGE", message="No valid bird image provided.")
            )

        try:
            raw_predictions = run_local_species_classifier(raw_bytes, target_group="bird")

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
            ident_status = "HIGH_CONFIDENCE" if top_score >= 0.80 else ("MEDIUM_CONFIDENCE" if top_score >= 0.50 else "LOW_CONFIDENCE")

            return PredictionResponse(
                success=True,
                category="bird",
                detected_category="bird",
                provider="legacy_bird_ai",
                model_name="PyTorch Avian Vision Classifier (Legacy)",
                model_version="v1.0",
                identification_status=ident_status,
                predictions=predictions,
                is_mock=False
            )

        except Exception as exc:
            print(f"Legacy bird classifier error: {exc}")
            return PredictionResponse(
                success=False,
                category="bird",
                provider="legacy_bird_ai",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                is_mock=False,
                error=ErrorDetail(
                    code="BIRD_PROVIDER_UNAVAILABLE",
                    message=f"Legacy bird classifier inference error: {str(exc)}"
                )
            )


class BirdProvider(IdentificationProvider):
    """
    Main Bird Identification Provider Router.
    Routes inference requests to BioCLIPBirdProvider (BioCLIP 2) when configured,
    or LegacyBirdProvider / MockProvider based on settings.
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

        provider_choice = getattr(settings, "BIRD_IDENTIFICATION_PROVIDER", "legacy_pytorch").lower()

        if provider_choice in ("legacy_pytorch", "local_ai", "legacy", "pytorch"):
            print("[IDENTIFY] Category: bird")
            print("[IDENTIFY] Provider: LegacyBirdProvider")
            return self.legacy_provider.identify(images, category=category, location=location)
        elif provider_choice == "bioclip":
            print("[IDENTIFY] Category: bird")
            print("[IDENTIFY] Provider: BioCLIPBirdProvider")
            from app.services.identification.bioclip import BioCLIPBirdProvider
            return BioCLIPBirdProvider().identify(images, category=category, location=location)
        else:
            print("[IDENTIFY] Category: bird")
            print("[IDENTIFY] Provider: LegacyBirdProvider")
            return self.legacy_provider.identify(images, category=category, location=location)

