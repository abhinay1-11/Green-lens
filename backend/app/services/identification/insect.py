import io
import os
from typing import List, Optional, Dict, Any

from app.config import settings
from app.services.identification.base import IdentificationProvider
from app.services.identification.mock import MockProvider
from app.services.identification.insect_model import run_insect_species_classifier
from app.schemas.identification import PredictionResponse, PredictionItem, ErrorDetail
from app.utils.confidence import normalize_confidence


class InsectProvider(IdentificationProvider):
    """
    Insect & Arthropod Identification Provider.
    Uses dedicated Insect EfficientNet-B0 ONNX Classifier by default for low-memory Render CPU deployment.
    Optional BioCLIP 2 TreeOfLifeClassifier when explicitly configured.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.mock_provider = MockProvider()

    def identify(
        self,
        images: List[Dict[str, Any]],
        category: str = "insect",
        location: Optional[Dict[str, float]] = None
    ) -> PredictionResponse:
        # Explicit mock mode check
        if settings.IDENTIFICATION_MODE == "mock":
            res = self.mock_provider.identify(images, category="insect", location=location)
            res.detected_category = "insect"
            return res

        if not images or not (images[0].get("file_bytes") or images[0].get("saved_path")):
            return PredictionResponse(
                success=False,
                category="insect",
                provider="insect_local_onnx",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                error=ErrorDetail(code="INVALID_IMAGE", message="No valid insect image provided.")
            )

        provider_choice = getattr(settings, "INSECT_IDENTIFICATION_PROVIDER", "local_onnx").lower()

        # 1. BioCLIP 2 Insecta Vision Engine (only if explicitly configured as bioclip)
        if provider_choice == "bioclip":
            print("[IDENTIFY] Category: insect")
            print("[IDENTIFY] Provider: BioCLIPInsectClassifier")
            try:
                from app.services.identification.bioclip import BioCLIPModelSingleton
                from PIL import Image
                from bioclip import Rank

                classifier = BioCLIPModelSingleton.get_classifier()
                first_img = images[0]
                if first_img.get("file_bytes"):
                    pil_image = Image.open(io.BytesIO(first_img["file_bytes"]))
                elif first_img.get("saved_path") and os.path.exists(first_img["saved_path"]):
                    pil_image = Image.open(first_img["saved_path"])
                else:
                    pil_image = None

                if pil_image:
                    if pil_image.mode != "RGB":
                        pil_image = pil_image.convert("RGB")

                    tax_filter = classifier.create_taxa_filter(Rank.CLASS, ["Insecta", "Arachnida"])
                    classifier.apply_filter(tax_filter)

                    raw_predictions = classifier.predict([pil_image], rank=Rank.SPECIES, k=5)
                    predictions = []
                    for idx, item in enumerate(raw_predictions, start=1):
                        sci_name = item.get("species") or f"{item.get('genus', '')} {item.get('species_epithet', '')}".strip() or "Unknown species"
                        raw_common = item.get("common_name", "").strip() if item.get("common_name") else ""
                        common_names = [raw_common] if raw_common else [sci_name]
                        score = float(item.get("score", 0.0))
                        norm_score = normalize_confidence(score)
                        predictions.append(
                            PredictionItem(
                                rank=idx,
                                scientific_name=sci_name,
                                common_names=common_names,
                                confidence=norm_score,
                                taxonomic_rank="species"
                            )
                        )

                    if predictions:
                        top_score = predictions[0].confidence
                        ident_status = "HIGH_CONFIDENCE" if top_score >= 0.80 else ("MEDIUM_CONFIDENCE" if top_score >= 0.50 else "LOW_CONFIDENCE")
                        return PredictionResponse(
                            success=True,
                            category="insect",
                            detected_category="insect",
                            provider="BioCLIP 2 (Insecta Vision)",
                            model_name="BioCLIP 2 TreeOfLife Insecta Classifier",
                            model_version="v2.0",
                            identification_status=ident_status,
                            predictions=predictions,
                            is_mock=False
                        )

            except Exception as bio_err:
                print(f"[InsectProvider] BioCLIP 2 engine unavailable, using fast local ONNX fallback: {bio_err}")

        # 2. Dedicated Insect EfficientNet-B0 ONNX Classifier (default for free tier)
        print("[IDENTIFY] Category: insect")
        print("[IDENTIFY] Provider: Insect EfficientNet-B0 ONNX Classifier")
        try:
            raw_bytes = images[0].get("file_bytes")
            if not raw_bytes and images[0].get("saved_path") and os.path.exists(images[0]["saved_path"]):
                with open(images[0]["saved_path"], "rb") as f:
                    raw_bytes = f.read()

            if not raw_bytes:
                raise ValueError("No image bytes available for inference.")

            raw_preds = run_insect_species_classifier(raw_bytes, top_k=5)

            if not raw_preds:
                return PredictionResponse(
                    success=False,
                    category="insect",
                    detected_category="insect",
                    provider="insect_local_onnx",
                    model_name="Insect EfficientNet-B0 ONNX Classifier",
                    model_version="v1.0",
                    identification_status="IDENTIFICATION_UNAVAILABLE",
                    predictions=[],
                    is_mock=False,
                    error=ErrorDetail(
                        code="NO_INSECT_DETECTED",
                        message="No insect could be identified with sufficient confidence."
                    )
                )

            top_pred = raw_preds[0]
            # Handle non-insect background predictions
            if top_pred.get("is_non_insect") or top_pred.get("taxonomic_rank") == "non_insect":
                return PredictionResponse(
                    success=False,
                    category="insect",
                    detected_category="insect",
                    provider="insect_local_onnx",
                    model_name="Insect EfficientNet-B0 ONNX Classifier",
                    model_version="v1.0",
                    identification_status="IDENTIFICATION_UNAVAILABLE",
                    predictions=[],
                    is_mock=False,
                    error=ErrorDetail(
                        code="NO_INSECT_DETECTED",
                        message=f"Image classified as non-insect background ({top_pred.get('common_name')})."
                    )
                )

            predictions = []
            for idx, item in enumerate(raw_preds, start=1):
                if item.get("is_non_insect") or item.get("taxonomic_rank") == "non_insect":
                    continue

                sci_name = item.get("scientific_name") or item.get("common_name")
                predictions.append(
                    PredictionItem(
                        rank=idx,
                        scientific_name=sci_name,
                        common_names=[item.get("common_name")],
                        confidence=float(item.get("confidence", 0.0)),
                        taxonomic_rank=item.get("taxonomic_rank", "category")
                    )
                )

            if not predictions:
                return PredictionResponse(
                    success=False,
                    category="insect",
                    detected_category="insect",
                    provider="insect_local_onnx",
                    model_name="Insect EfficientNet-B0 ONNX Classifier",
                    model_version="v1.0",
                    identification_status="IDENTIFICATION_UNAVAILABLE",
                    predictions=[],
                    is_mock=False,
                    error=ErrorDetail(
                        code="NO_INSECT_DETECTED",
                        message="No insect targets detected in image."
                    )
                )

            top_score = predictions[0].confidence
            ident_status = "HIGH_CONFIDENCE" if top_score >= 0.80 else ("MEDIUM_CONFIDENCE" if top_score >= 0.50 else "LOW_CONFIDENCE")

            return PredictionResponse(
                success=True,
                category="insect",
                detected_category="insect",
                provider="insect_local_onnx",
                model_name="Insect EfficientNet-B0 ONNX Classifier",
                model_version="v1.0",
                identification_status=ident_status,
                predictions=predictions,
                is_mock=False,
            )

        except Exception as exc:
            print(f"Insect ONNX classifier error: {exc}")
            return PredictionResponse(
                success=False,
                category="insect",
                provider="insect_local_onnx",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                is_mock=False,
                error=ErrorDetail(
                    code="INSECT_PROVIDER_UNAVAILABLE",
                    message=f"Insect species classifier inference error: {str(exc)}"
                )
            )
