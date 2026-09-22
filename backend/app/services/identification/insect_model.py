import logging
from typing import List, Dict, Any
import numpy as np

from app.services.identification.local_model import run_local_species_classifier, _preprocess_image

logger = logging.getLogger("greenlens.identification.insect_model")


def preprocess_insect_image(image_bytes: bytes, target_size: int = 224) -> np.ndarray:
    """
    Validates, converts to RGB, applies EXIF orientation and normalizes input image
    using canonical MobileNetV3-Small ImageNet preprocessing.
    """
    return _preprocess_image(image_bytes)


def run_insect_species_classifier(image_bytes: bytes, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Executes MobileNetV3-Small ImageNet inference via local_model service.
    Returns list of predicted species dicts.
    """
    raw_preds = run_local_species_classifier(image_bytes, target_group="insect")

    results = []
    for idx, (sci_name, common_name, score) in enumerate(raw_preds[:top_k]):
        results.append({
            "index": idx,
            "label": common_name.lower().replace(" ", "_"),
            "common_name": common_name,
            "scientific_name": sci_name,
            "taxonomic_rank": "species",
            "confidence": float(score),
            "is_non_insect": False
        })

    return results


