import io
import os
import time
import threading
from typing import List, Optional, Dict, Any
from PIL import Image

from app.config import settings
from app.services.identification.base import IdentificationProvider
from app.schemas.identification import PredictionResponse, PredictionItem, ErrorDetail
from app.utils.confidence import normalize_confidence


class BioCLIPModelSingleton:
    """
    Thread-safe Singleton wrapper around BioCLIP 2 TreeOfLifeClassifier.
    Initialized at FastAPI application startup and cached permanently in memory.
    Reuses existing Hugging Face cached resources (~4.5 GB).
    """
    _instance = None
    _lock = threading.Lock()
    _classifier = None
    _load_error = None

    @classmethod
    def get_classifier(cls):
        if cls._classifier is None and cls._load_error is None:
            with cls._lock:
                if cls._classifier is None and cls._load_error is None:
                    try:
                        print("[BioCLIP] Loading BioCLIP 2 model and tree-of-life embeddings...")
                        t0 = time.time()
                        from bioclip import TreeOfLifeClassifier
                        cls._classifier = TreeOfLifeClassifier()
                        print(f"[BioCLIP] BioCLIP 2 model loaded successfully in {time.time() - t0:.2f}s")
                    except Exception as exc:
                        print(f"[BioCLIP] Failed to initialize BioCLIP 2 model: {exc}")
                        cls._load_error = str(exc)
                        raise exc
        if cls._load_error:
            raise RuntimeError(f"BioCLIP 2 model initialization failed: {cls._load_error}")
        return cls._classifier


class BioCLIPBirdProvider(IdentificationProvider):
    """
    Bird Species Identification Provider powered by BioCLIP 2 (imageomics/bioclip-2).
    Uses TreeOfLifeClassifier for species-level inference across 10,000+ avian species.
    """

    def __init__(self):
        pass

    def identify(
        self,
        images: List[Dict[str, Any]],
        category: str = "bird",
        location: Optional[Dict[str, float]] = None
    ) -> PredictionResponse:
        # Explicit mock mode check
        if settings.IDENTIFICATION_MODE == "mock":
            from app.services.identification.mock import MockProvider
            res = MockProvider().identify(images, category="bird", location=location)
            res.detected_category = "bird"
            return res

        if not images or not (images[0].get("file_bytes") or images[0].get("saved_path")):
            return PredictionResponse(
                success=False,
                category="bird",
                detected_category="bird",
                provider="BioCLIP 2",
                model_name="BioCLIP 2 (imageomics/bioclip-2)",
                model_version="2.0.0",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                is_mock=False,
                error=ErrorDetail(code="INVALID_IMAGE", message="No valid bird image provided.")
            )

        try:
            print("[BioCLIP] Running BioCLIP 2 bird identification pipeline...")
            
            # Stage 1: Model Initialization Check
            t_init_start = time.time()
            classifier = BioCLIPModelSingleton.get_classifier()
            t_init_end = time.time()
            init_time = t_init_end - t_init_start

            # Stage 2: Preprocessing
            t_prep_start = time.time()
            first_img = images[0]
            if first_img.get("file_bytes"):
                pil_image = Image.open(io.BytesIO(first_img["file_bytes"]))
            elif first_img.get("saved_path") and os.path.exists(first_img["saved_path"]):
                pil_image = Image.open(first_img["saved_path"])
            else:
                raise ValueError("Image source is invalid or unreadable.")

            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")
            t_prep_end = time.time()
            prep_time = t_prep_end - t_prep_start

            # Stage 3: Inference
            t_infer_start = time.time()
            from bioclip import Rank
            raw_predictions = classifier.predict([pil_image], rank=Rank.SPECIES, k=5)
            t_infer_end = time.time()
            infer_time = t_infer_end - t_infer_start

            # Stage 4: Taxonomy Mapping & Score Normalization
            t_tax_start = time.time()
            predictions: List[PredictionItem] = []
            print(f"[BioCLIP Debug Log] raw candidates count: {len(raw_predictions)}")
            for idx, item in enumerate(raw_predictions, start=1):
                sci_name = item.get("species") or f"{item.get('genus', '')} {item.get('species_epithet', '')}".strip() or "Unknown species"
                raw_common = item.get("common_name", "").strip() if item.get("common_name") else ""
                common_names = [raw_common] if raw_common else []

                raw_score = float(item.get("score", 0.0))
                norm_confidence = normalize_confidence(raw_score)
                print(f"Candidate {idx}: scientific_name = '{sci_name}' | raw_score = {raw_score:.4f} | normalized_confidence = {norm_confidence:.4f}")

                predictions.append(
                    PredictionItem(
                        rank=idx,
                        scientific_name=sci_name,
                        common_names=common_names,
                        confidence=norm_confidence,
                        taxonomic_rank="species"
                    )
                )

            top_confidence = predictions[0].confidence if predictions else 0.0
            min_thresh = getattr(settings, "BIRD_MIN_CONFIDENCE", 0.30)

            if top_confidence < min_thresh:
                ident_status = "LOW_CONFIDENCE"
            elif top_confidence >= 0.80:
                ident_status = "HIGH_CONFIDENCE"
            else:
                ident_status = "MEDIUM_CONFIDENCE"
            t_tax_end = time.time()
            tax_time = t_tax_end - t_tax_start

            response = PredictionResponse(
                success=True,
                category="bird",
                detected_category="bird",
                provider="BioCLIP 2",
                model_name="BioCLIP 2 (imageomics/bioclip-2)",
                model_version="2.0.0",
                identification_status=ident_status,
                predictions=predictions,
                is_mock=False
            )
            
            # Store timing stats for performance reporting
            response._perf_details = {
                "model_initialization": init_time,
                "preprocessing": prep_time,
                "inference": infer_time,
                "taxonomy": tax_time
            }
            return response

        except Exception as exc:
            print(f"[BioCLIP] Prediction error: {exc}")
            return PredictionResponse(
                success=False,
                category="bird",
                detected_category="bird",
                provider="BioCLIP 2",
                model_name="BioCLIP 2 (imageomics/bioclip-2)",
                model_version="2.0.0",
                identification_status="IDENTIFICATION_UNAVAILABLE",
                predictions=[],
                is_mock=False,
                error=ErrorDetail(
                    code="BIRD_PROVIDER_UNAVAILABLE",
                    message="Bird identification service is temporarily unavailable."
                )
            )
