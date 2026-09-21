import io
import os
import json
from pathlib import Path
from typing import List, Tuple
import numpy as np
from PIL import Image, ImageOps

_SESSION = None
_INPUT_NAME = None
_OUTPUT_NAME = None
_ID2LABEL = None

MODEL_PATH = Path(__file__).resolve().parents[3] / "models" / "bird_species.onnx"
CONFIG_PATH = Path(__file__).resolve().parents[3] / "models" / "bird_species_config.json"

# Image preprocessing constants from model preprocessor config
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 1, 3)
STD = np.array([0.47853944, 0.4732864, 0.47434163], dtype=np.float32).reshape(1, 1, 3)

def _load_bird_model():
    """
    Lazy loads and caches the ONNX Runtime session for the bird species classifier.
    Uses CPUExecutionProvider with low thread count to conserve Render CPU/RAM.
    """
    global _SESSION, _INPUT_NAME, _OUTPUT_NAME, _ID2LABEL

    if _SESSION is None:
        import onnxruntime as ort

        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Bird ONNX model file not found at {MODEL_PATH}")

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 1
        opts.inter_op_num_threads = 1

        _SESSION = ort.InferenceSession(
            str(MODEL_PATH),
            sess_options=opts,
            providers=["CPUExecutionProvider"]
        )
        _INPUT_NAME = _SESSION.get_inputs()[0].name
        _OUTPUT_NAME = _SESSION.get_outputs()[0].name

        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                _ID2LABEL = cfg.get("id2label", {})
        else:
            _ID2LABEL = {}

    return _SESSION, _INPUT_NAME, _OUTPUT_NAME, _ID2LABEL


def run_bird_species_classifier(image_bytes: bytes) -> List[Tuple[str, str, float]]:
    """
    Executes lightweight ONNX inference for bird species recognition.
    Returns list of (scientific_name, common_name, confidence_float).
    """
    session, input_name, output_name, id2label = _load_bird_model()

    image_stream = io.BytesIO(image_bytes)
    try:
        raw_img = Image.open(image_stream)
        img = ImageOps.exif_transpose(raw_img)

        # Preprocess: resize to 224x224 RGB
        img = img.convert("RGB").resize((224, 224), Image.Resampling.BILINEAR)

        # Convert to numpy float32 array in range [0, 1]
        img_np = np.array(img, dtype=np.float32) / 255.0

        # Normalize with ImageNet mean and std
        img_np = (img_np - MEAN) / STD

        # Transpose HWC (224, 224, 3) -> NCHW (1, 3, 224, 224)
        tensor = np.transpose(img_np, (2, 0, 1))[np.newaxis, :, :, :].astype(np.float32)

        # Run ONNX inference
        logits = session.run([output_name], {input_name: tensor})[0][0]

        # Compute softmax over logits
        exp_logits = np.exp(logits - np.max(logits))
        probabilities = exp_logits / np.sum(exp_logits)

        # Get top 5 predictions
        top5_indices = np.argsort(probabilities)[::-1][:5]

        results = []
        for idx in top5_indices:
            score = float(probabilities[idx])
            raw_label = id2label.get(str(idx), f"Bird Species {idx}")
            clean_name = raw_label.strip().title()

            # Format as (scientific_name, common_name, score)
            results.append((clean_name, clean_name, score))

        return results

    finally:
        image_stream.close()
