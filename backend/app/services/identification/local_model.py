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
# INSECT & ARTHROPOD TAXONOMY MAP
# ============================================================

INSECT_ARTHROPOD_TAXONOMY_MAP = {
    71: ("Centruroides sculpturatus", "Arizona Bark Scorpion"),
    72: ("Argiope aurantia", "Black and Yellow Garden Spider"),
    73: ("Araneus cavaticus", "Barn Spider"),
    74: ("Araneus diadematus", "European Garden Spider"),
    76: ("Aphonopelma chalcodes", "Western Desert Tarantula"),
    77: ("Hogna carolinensis", "Carolina Wolf Spider"),
    78: ("Ixodes scapularis", "Blacklegged Tick"),
    79: ("Scolopendra heros", "Giant Desert Centipede"),
    300: ("Cicindela sexguttata", "Six-spotted Tiger Beetle"),
    301: ("Coccinella septempunctata", "Seven-spot Ladybird"),
    302: ("Carabidae", "Ground Beetle"),
    303: ("Anoplophora glabripennis", "Asian Long-horned Beetle"),
    304: ("Chrysomelidae", "Leaf Beetle"),
    305: ("Scarabaeus sacer", "Sacred Dung Beetle"),
    306: ("Oryctes nasicornis", "European Rhinoceros Beetle"),
    307: ("Curculio nucum", "Nut Weevil"),
    308: ("Musca domestica", "House Fly"),
    309: ("Apis mellifera", "Western Honey Bee"),
    310: ("Solenopsis invicta", "Red Imported Fire Ant"),
    311: ("Melanoplus differentialis", "Differential Grasshopper"),
    312: ("Acheta domesticus", "House Cricket"),
    313: ("Diapheromera femorata", "Northern Walkingstick"),
    314: ("Periplaneta americana", "American Cockroach"),
    315: ("Mantis religiosa", "European Praying Mantis"),
    316: ("Magicicada septendecim", "Periodical Cicada"),
    317: ("Cicadellidae", "Leafhopper"),
    318: ("Chrysoperla carnea", "Common Green Lacewing"),
    319: ("Anax junius", "Green Darner Dragonfly"),
    320: ("Calopteryx maculata", "Ebony Jewelwing Damselfly"),
    321: ("Vanessa atalanta", "Red Admiral Butterfly"),
    322: ("Aphantopus hyperantus", "Ringlet Butterfly"),
    323: ("Danaus plexippus", "Monarch Butterfly"),
    324: ("Pieris rapae", "Cabbage White Butterfly"),
    325: ("Phoebis sennae", "Cloudless Sulphur Butterfly"),
    326: ("Celastrina ladon", "Spring Azure Butterfly"),
}

INSECT_CLASS_INDICES = sorted(list(INSECT_ARTHROPOD_TAXONOMY_MAP.keys()))


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
    """
    Canonical preprocessing pipeline for MobileNetV3-Small ImageNet:
    1. Decode raw bytes
    2. EXIF orientation correction
    3. RGB conversion
    4. Resolution validation
    5. Aspect-ratio preserving thumbnail downsample
    6. 256x256 resize + 224x224 center crop
    7. ImageNet mean/std normalization -> NCHW Float32 tensor (1, 3, 224, 224)
    """
    try:
        original = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(original)
    except Exception as exc:
        raise ValueError("UNREADABLE_IMAGE: Unable to decode image bytes.") from exc

    w, h = img.size
    if w < 16 or h < 16:
        raise ValueError("IMAGE_TOO_SMALL: Image resolution is too low for reliable identification.")

    img.thumbnail((384, 384), Image.Resampling.BILINEAR)
    img = img.convert("RGB")
    img = img.resize((256, 256), Image.Resampling.BILINEAR)

    left = (256 - INPUT_SIZE) // 2
    top = (256 - INPUT_SIZE) // 2
    right = left + INPUT_SIZE
    bottom = top + INPUT_SIZE

    img = img.crop((left, top, right, bottom))
    array = np.asarray(img, dtype=np.float32)

    array /= 255.0
    array = (array - MEAN) / STD
    array = np.transpose(array, (2, 0, 1))
    array = np.expand_dims(array, axis=0).astype(np.float32)

    return array


def _softmax(logits: np.ndarray) -> np.ndarray:
    logits = np.asarray(logits, dtype=np.float32)
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
    """
    Executes lightweight ONNX MobileNetV3-Small ImageNet inference.
    """
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

        results = []

        if target_group == "insect":
            print("INSECT MODEL: MobileNetV3-Small ImageNet")

            # Extract insect sub-taxonomy logits & calculate softmax probabilities
            insect_logits = logits[INSECT_CLASS_INDICES]
            insect_probs = _softmax(insect_logits)

            top_count = min(5, len(INSECT_CLASS_INDICES))
            top_positions = np.argsort(insect_probs)[::-1][:top_count]

            for pos in top_positions:
                category_index = INSECT_CLASS_INDICES[int(pos)]
                score = float(insect_probs[pos])
                mapped = INSECT_ARTHROPOD_TAXONOMY_MAP.get(category_index)

                if mapped is not None:
                    scientific_name, common_name = mapped
                else:
                    fallback_name = categories[category_index]
                    scientific_name = fallback_name
                    common_name = _clean_category_name(fallback_name)

                results.append((scientific_name, common_name, score))

        else:
            probabilities = _softmax(logits)
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