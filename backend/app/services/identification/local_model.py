import io
import gc
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageOps
import onnxruntime as ort


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = (
    Path(__file__).resolve().parents[3]
    / "models"
    / "mobilenet_v3_small.onnx"
)

INPUT_SIZE = 224

MEAN = np.array(
    [0.485, 0.456, 0.406],
    dtype=np.float32,
).reshape(1, 1, 3)

STD = np.array(
    [0.229, 0.224, 0.225],
    dtype=np.float32,
).reshape(1, 1, 3)


# ============================================================
# GLOBAL MODEL STATE
# ============================================================

_SESSION = None
_INPUT_NAME = None
_OUTPUT_NAME = None
_CATEGORIES = None


def _load_categories():
    global _CATEGORIES

    if _CATEGORIES is not None:
        return _CATEGORIES

    category_file = (
        Path(__file__).resolve().parents[3]
        / "models"
        / "imagenet_classes.txt"
    )

    if category_file.exists():
        try:
            with open(category_file, "r", encoding="utf-8") as f:
                categories = [
                    line.strip()
                    for line in f
                    if line.strip()
                ]

            if len(categories) >= 1000:
                _CATEGORIES = categories[:1000]
                return _CATEGORIES

        except Exception:
            pass

    _CATEGORIES = [
        f"ImageNet class {i}"
        for i in range(1000)
    ]

    return _CATEGORIES


def _load_model():
    global _SESSION
    global _INPUT_NAME
    global _OUTPUT_NAME

    if _SESSION is not None:
        return _SESSION, _INPUT_NAME, _OUTPUT_NAME

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"ONNX model not found: {MODEL_PATH}."
        )

    session_options = ort.SessionOptions()
    session_options.intra_op_num_threads = 1
    session_options.inter_op_num_threads = 1
    session_options.enable_cpu_mem_arena = True
    session_options.enable_mem_pattern = True

    _SESSION = ort.InferenceSession(
        str(MODEL_PATH),
        sess_options=session_options,
        providers=["CPUExecutionProvider"],
    )

    _INPUT_NAME = _SESSION.get_inputs()[0].name
    _OUTPUT_NAME = _SESSION.get_outputs()[0].name

    return _SESSION, _INPUT_NAME, _OUTPUT_NAME


def _preprocess_image(image_bytes: bytes) -> np.ndarray:
    with Image.open(io.BytesIO(image_bytes)) as original:
        img = ImageOps.exif_transpose(original)
        img.thumbnail(
            (384, 384),
            Image.Resampling.BILINEAR,
        )
        img = img.convert("RGB")
        img = img.resize(
            (256, 256),
            Image.Resampling.BILINEAR,
        )

        left = (256 - INPUT_SIZE) // 2
        top = (256 - INPUT_SIZE) // 2
        right = left + INPUT_SIZE
        bottom = top + INPUT_SIZE

        img = img.crop(
            (left, top, right, bottom)
        )

        array = np.asarray(
            img,
            dtype=np.float32,
        )

    array /= 255.0
    array = (array - MEAN) / STD
    array = np.transpose(
        array,
        (2, 0, 1),
    )
    array = np.expand_dims(
        array,
        axis=0,
    ).astype(np.float32)

    return array


def _softmax(logits: np.ndarray) -> np.ndarray:
    logits = np.asarray(
        logits,
        dtype=np.float32,
    )
    logits = logits - np.max(logits)
    exp_values = np.exp(logits)
    return exp_values / np.sum(exp_values)


def _clean_category_name(name: str) -> str:
    return (
        name
        .replace("_", " ")
        .replace(",", ", ")
        .strip()
        .title()
    )


def run_local_species_classifier(
    image_bytes: bytes,
    target_group: str = "general",
) -> List[Tuple[str, str, float]]:
    session = None
    input_tensor = None
    output = None

    try:
        session, input_name, output_name = _load_model()
        categories = _load_categories()
        input_tensor = _preprocess_image(image_bytes)

        outputs = session.run(
            [output_name],
            {input_name: input_tensor},
        )
        output = outputs[0]

        logits = np.asarray(
            output[0],
            dtype=np.float32,
        )
        probabilities = _softmax(logits)

        results = []
        top_count = min(5, len(probabilities))
        top_indices = np.argsort(probabilities)[::-1][:top_count]

        for category_index in top_indices:
            score = float(probabilities[category_index])
            category_name = categories[int(category_index)]
            clean_name = _clean_category_name(category_name)
            results.append((clean_name, clean_name, score))

        return results

    finally:
        input_tensor = None
        output = None
        gc.collect()