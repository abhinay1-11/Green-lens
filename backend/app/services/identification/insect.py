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
                        ident_status = "HIGH_CONFIDENCE" if top_score >= 0.70 else ("MEDIUM_CONFIDENCE" if top_score >= 0.40 else "LOW_CONFIDENCE")
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

            raw_preds = run_insect_species_classifier(raw_bytes, top_k=27)

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

            bg_indices = {20, 21, 22, 23}
            insect_preds = [p for p in raw_preds if p.get("index") not in bg_indices and not p.get("is_non_insect")]
            bg_preds = [p for p in raw_preds if p.get("index") in bg_indices or p.get("is_non_insect")]

            best_insect_conf = insect_preds[0]["confidence"] if insect_preds else 0.0
            best_bg_conf = bg_preds[0]["confidence"] if bg_preds else 0.0
            margin = best_bg_conf - best_insect_conf

            # Two-stage decision policy: Reject as non-insect ONLY when background is genuinely decisive
            if best_bg_conf >= 0.85 and margin >= 0.30:
                bg_name = bg_preds[0]["common_name"] if bg_preds else "Background"
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
                        message=f"Image classified as non-insect background ({bg_name})."
                    )
                )

            predictions = []
            for idx, item in enumerate(insect_preds[:5], start=1):
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
