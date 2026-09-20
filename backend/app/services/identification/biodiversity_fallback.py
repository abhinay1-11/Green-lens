from typing import List, Optional, Dict, Any

from app.config import settings
from app.services.identification.base import IdentificationProvider
from app.services.identification.local_model import run_local_species_classifier
from app.schemas.identification import PredictionResponse, PredictionItem, ErrorDetail
from app.utils.confidence import normalize_confidence

class BiodiversityFallbackProvider(IdentificationProvider):
    """
    General Biodiversity Fallback Model Provider.
    Executes PyTorch pretrained general species vision classifier across all taxonomic groups.
    Requires NO external API key or network connection.
    """

    def identify(
        self,
        images: List[Dict[str, Any]],
        category: str = "general",
        location: Optional[Dict[str, float]] = None
    ) -> PredictionResponse:
        if not images or not images[0].get("file_bytes"):
            return PredictionResponse(
                success=False,
                category=category,
                provider="biodiversity_fallback",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                is_mock=False,
                error=ErrorDetail(code="INVALID_IMAGE", message="No valid image provided for biodiversity fallback.")
            )

        try:
            raw_bytes = images[0]["file_bytes"]
            raw_predictions = run_local_species_classifier(raw_bytes, target_group="general")

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
                category=category,
                provider="biodiversity_fallback_ai",
                model_name="PyTorch General Biodiversity Classifier",
                model_version="v1.0",
                identification_status=ident_status,
                predictions=predictions,
                is_mock=False
            )

        except Exception as exc:
            print(f"Biodiversity Fallback error: {exc}")

        return PredictionResponse(
            success=False,
            category=category,
            provider="biodiversity_fallback",
            identification_status="IDENTIFICATION_UNAVAILABLE",
            predictions=[],
            is_mock=False,
            error=ErrorDetail(
                code="FALLBACK_PROVIDER_UNAVAILABLE",
                message="Biodiversity fallback service is currently unavailable."
            )
        )
