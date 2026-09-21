import os
import io
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from PIL import Image, ImageOps
import onnxruntime as ort

logger = logging.getLogger("greenlens.identification.insect_model")

_INSECT_SESSION: Optional[ort.InferenceSession] = None
_INSECT_CONFIG: Optional[Dict[str, Any]] = None

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "insect_species.onnx")
CONFIG_PATH = os.path.join(MODEL_DIR, "insect_species_config.json")


def _get_insect_config() -> Dict[str, Any]:
    global _INSECT_CONFIG
    if _INSECT_CONFIG is None:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                _INSECT_CONFIG = json.load(f)
        else:
            logger.warning("Insect config file not found at %s. Falling back to empty dict.", CONFIG_PATH)
            _INSECT_CONFIG = {}
    return _INSECT_CONFIG


def _get_insect_session() -> ort.InferenceSession:
    global _INSECT_SESSION
    if _INSECT_SESSION is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Insect ONNX model not found at {MODEL_PATH}")

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 1
        opts.inter_op_num_threads = 1
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        _INSECT_SESSION = ort.InferenceSession(
            MODEL_PATH,
            sess_options=opts,
            providers=["CPUExecutionProvider"]
        )
        logger.info("Loaded Insect EfficientNet-B0 ONNX session successfully.")
    return _INSECT_SESSION


def run_insect_species_classifier(image_bytes: bytes, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Runs insect classification using the EfficientNet-B0 ONNX model.
    Returns a list of dicts containing class metadata and confidence scores.
    """
    session = _get_insect_session()
    config = _get_insect_config()

    # Preprocess image
    image = Image.open(io.BytesIO(image_bytes))
    image = ImageOps.exif_transpose(image).convert("RGB")
    image = image.resize((128, 128), Image.Resampling.BILINEAR)

    img_np = np.array(image, dtype=np.float32) / 255.0
    img_np = np.transpose(img_np, (2, 0, 1))  # HWC to CHW
    img_np = np.expand_dims(img_np, axis=0)     # Add batch dimension [1, 3, 128, 128]

    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: img_np})[0][0]

    # Apply Softmax over 27 classes
    exp_logits = np.exp(outputs - np.max(outputs))
    probabilities = exp_logits / np.sum(exp_logits)

    top_indices = np.argsort(probabilities)[::-1][:top_k]

    results = []
    for idx in top_indices:
        idx_str = str(idx)
        class_info = config.get(idx_str, {
            "label": f"class_{idx}",
            "common_name": f"Insect Group {idx}",
            "scientific_name": None,
            "taxonomic_rank": "category"
        })

        conf = float(probabilities[idx])
        is_non_insect = class_info.get("taxonomic_rank") == "non_insect"

        results.append({
            "index": int(idx),
            "label": class_info["label"],
            "common_name": class_info["common_name"],
            "scientific_name": class_info.get("scientific_name"),
            "taxonomic_rank": class_info.get("taxonomic_rank", "category"),
            "confidence": conf,
            "is_non_insect": is_non_insect
        })

    return results
