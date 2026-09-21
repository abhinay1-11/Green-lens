import os
import io
import json
import logging
import threading
from typing import List, Dict, Any, Optional
import numpy as np
from PIL import Image, ImageOps

logger = logging.getLogger("greenlens.identification.insect_model")

_INSECT_SESSION: Optional[Any] = None
_INSECT_CONFIG: Optional[Dict[str, Any]] = None
_INSECT_LOCK = threading.Lock()

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models"))
MODEL_PATH = os.path.join(MODEL_DIR, "insect_species.onnx")
CONFIG_PATH = os.path.join(MODEL_DIR, "insect_species_config.json")


def _get_insect_config() -> Dict[str, Any]:
    global _INSECT_CONFIG
    if _INSECT_CONFIG is None:
        with _INSECT_LOCK:
            if _INSECT_CONFIG is None:
                if os.path.exists(CONFIG_PATH):
                    try:
                        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                            _INSECT_CONFIG = json.load(f)
                    except Exception as e:
                        logger.error("[Insect ONNX] Failed to load config JSON: %s", e)
                        _INSECT_CONFIG = {}
                else:
                    logger.warning("[Insect ONNX] Config file not found at %s. Using empty fallback.", CONFIG_PATH)
                    _INSECT_CONFIG = {}
    return _INSECT_CONFIG


def _get_insect_session():
    global _INSECT_SESSION
    if _INSECT_SESSION is None:
        with _INSECT_LOCK:
            if _INSECT_SESSION is None:
                if not os.path.exists(MODEL_PATH):
                    raise FileNotFoundError(f"Insect ONNX model file not found at {MODEL_PATH}")

                logger.info("[Insect ONNX] Loading EfficientNet-B0 model...")
                import onnxruntime as ort

                opts = ort.SessionOptions()
                opts.intra_op_num_threads = 1
                opts.inter_op_num_threads = 1
                opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                opts.enable_cpu_mem_arena = True
                opts.enable_mem_pattern = True

                _INSECT_SESSION = ort.InferenceSession(
                    MODEL_PATH,
                    sess_options=opts,
                    providers=["CPUExecutionProvider"]
                )
                logger.info("[Insect ONNX] Model loaded successfully")
    return _INSECT_SESSION


def preprocess_insect_image(image_bytes: bytes, target_size: int = 128) -> np.ndarray:
    """
    Validates, converts to RGB, and letterboxes input image to target_size x target_size
    preserving exact aspect ratio without organism distortion.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image)
    except Exception as e:
        raise ValueError("UNREADABLE_IMAGE: Unable to read image file.") from e

    if image.mode != "RGB":
        image = image.convert("RGB")

    w, h = image.size
    if w < 16 or h < 16:
        raise ValueError("IMAGE_TOO_SMALL: Image resolution is too low for reliable identification. Please upload a clearer image.")

    # Aspect-ratio preserving resize with letterbox padding
    scale = target_size / float(max(w, h))
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    resized = image.resize((new_w, new_h), Image.Resampling.BILINEAR)

    # Neutral gray background canvas (128, 128, 128)
    padded = Image.new("RGB", (target_size, target_size), (128, 128, 128))
    pad_x = (target_size - new_w) // 2
    pad_y = (target_size - new_h) // 2
    padded.paste(resized, (pad_x, pad_y))

    img_np = np.array(padded, dtype=np.float32) / 255.0
    img_np = np.transpose(img_np, (2, 0, 1))  # HWC -> CHW [3, 128, 128]
    img_np = np.expand_dims(img_np, axis=0)     # Batch dim [1, 3, 128, 128]
    return img_np


def run_insect_species_classifier(image_bytes: bytes, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Runs insect classification using the EfficientNet-B0 ONNX model.
    Model is lazy loaded on the first call. Subsequent calls reuse cached session.
    """
    session = _get_insect_session()
    config = _get_insect_config()

    img_np = preprocess_insect_image(image_bytes, target_size=128)

    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: img_np})[0][0]

    # Apply Softmax over logits
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

    top_res = results[0] if results else {}
    print(f"[Insect ONNX]\n"
          f"  input shape: {img_np.shape}\n"
          f"  input dtype: {img_np.dtype}\n"
          f"  input min/max: {img_np.min():.3f} / {img_np.max():.3f}\n"
          f"  output shape: {outputs.shape}\n"
          f"  top prediction: {top_res.get('common_name')} ({top_res.get('label')})\n"
          f"  top confidence: {top_res.get('confidence', 0.0):.4f}")

    return results

