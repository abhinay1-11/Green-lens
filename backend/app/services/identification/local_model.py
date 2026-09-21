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

# Expected location:
#
# backend/
# ├── app/
# │   └── services/
# │       └── identification/
# │           └── local_model.py
# │
# └── models/
#     └── mobilenet_v3_small.onnx
#
MODEL_PATH = (
    Path(__file__).resolve().parents[3]
    / "models"
    / "mobilenet_v3_small.onnx"
)

INPUT_SIZE = 224

# ImageNet normalization used by torchvision MobileNetV3-Small.
# These values match the official torchvision preprocessing.
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


# ============================================================
# IMAGENET CATEGORIES
# ============================================================
#
# IMPORTANT:
# MobileNetV3-Small ImageNet weights use the standard 1000
# ImageNet categories.
#
# We keep the categories required by the existing GreenLens
# classifier interface.
#
# The full category list is loaded from the optional file:
#
# backend/models/imagenet_classes.txt
#
# If that file is unavailable, the model can still run, but
# predictions will use ImageNet class IDs as fallback names.
#

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

    # Fallback.
    # The model still works, but unknown ImageNet classes are
    # represented by their numeric class index.
    _CATEGORIES = [
        f"ImageNet class {i}"
        for i in range(1000)
    ]

    return _CATEGORIES


# ============================================================
# BIRD CLASS INDICES
# ============================================================

# Existing GreenLens ImageNet bird class selection.
BIRD_CLASS_INDICES = sorted(
    list(
        set(range(8, 25))
        | set(range(80, 101))
        | set(range(127, 147))
    )
)


# ============================================================
# INSECT / ARTHROPOD TAXONOMY
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

INSECT_CLASS_INDICES = sorted(
    INSECT_ARTHROPOD_TAXONOMY_MAP.keys()
)


# ============================================================
# ONNX SESSION
# ============================================================

def _load_model():
    """
    Lazily loads the ONNX model.

    IMPORTANT:
    This does NOT import torch or torchvision.

    ONNX Runtime performs CPU inference directly.
    """

    global _SESSION
    global _INPUT_NAME
    global _OUTPUT_NAME

    if _SESSION is not None:
        return _SESSION, _INPUT_NAME, _OUTPUT_NAME

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"ONNX model not found: {MODEL_PATH}. "
            "Place mobilenet_v3_small.onnx inside backend/models/."
        )

    # Keep CPU thread usage low for Render Free.
    session_options = ort.SessionOptions()

    session_options.intra_op_num_threads = 1
    session_options.inter_op_num_threads = 1

    # Reduce unnecessary memory pressure.
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


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def _preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Converts uploaded image into MobileNetV3 input.

    Memory-safe strategy:
    1. Open image.
    2. Apply EXIF orientation.
    3. Resize BEFORE creating a large RGB copy.
    4. Convert to RGB.
    5. Resize/crop to 224x224.
    6. Normalize.
    7. Convert to NCHW float32.

    Returns:
        numpy array with shape (1, 3, 224, 224)
    """

    with Image.open(io.BytesIO(image_bytes)) as original:

        # Correct phone-camera orientation.
        img = ImageOps.exif_transpose(original)

        # Prevent huge camera images from creating huge RGB
        # allocations.
        img.thumbnail(
            (384, 384),
            Image.Resampling.BILINEAR,
        )

        # Now convert the much smaller image to RGB.
        img = img.convert("RGB")

        # Official MobileNetV3 preprocessing:
        # resize to 256 and center crop 224.
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

        # Convert directly to float32 NumPy.
        array = np.asarray(
            img,
            dtype=np.float32,
        )

    # Scale [0,255] -> [0,1]
    array /= 255.0

    # ImageNet normalization.
    array = (array - MEAN) / STD

    # HWC -> CHW
    array = np.transpose(
        array,
        (2, 0, 1),
    )

    # Add batch dimension.
    array = np.expand_dims(
        array,
        axis=0,
    ).astype(np.float32)

    return array


# ============================================================
# SOFTMAX
# ============================================================

def _softmax(logits: np.ndarray) -> np.ndarray:
    """
    Numerically stable softmax.
    """

    logits = np.asarray(
        logits,
        dtype=np.float32,
    )

    logits = logits - np.max(logits)

    exp_values = np.exp(logits)

    return exp_values / np.sum(exp_values)


# ============================================================
# CLASS NAME CLEANUP
# ============================================================

def _clean_category_name(name: str) -> str:
    """
    Converts ImageNet-style labels into readable names.
    """

    return (
        name
        .replace("_", " ")
        .replace(",", ", ")
        .strip()
        .title()
    )


# ============================================================
# LOCAL SPECIES CLASSIFIER
# ============================================================

def run_local_species_classifier(
    image_bytes: bytes,
    target_group: str = "bird",
) -> List[Tuple[str, str, float]]:
    """
    Executes lightweight ONNX MobileNetV3-Small inference.

    Parameters
    ----------
    image_bytes:
        Uploaded image bytes.

    target_group:
        "bird"
        "insect"
        "general"

    Returns
    -------
    List of:
        (scientific_name, common_name, confidence)
    """

    session = None
    input_tensor = None
    output = None

    try:
        # Load ONNX Runtime session lazily.
        session, input_name, output_name = _load_model()

        # Load ImageNet category labels.
        categories = _load_categories()

        # Memory-safe preprocessing.
        input_tensor = _preprocess_image(
            image_bytes
        )

        # ONNX Runtime inference.
        outputs = session.run(
            [output_name],
            {
                input_name: input_tensor,
            },
        )

        output = outputs[0]

        # Expected shape:
        # (1, 1000)
        logits = np.asarray(
            output[0],
            dtype=np.float32,
        )

        probabilities = _softmax(logits)

        results = []

        # ====================================================
        # BIRD
        # ====================================================

        if target_group == "bird":

            bird_probs = probabilities[
                BIRD_CLASS_INDICES
            ]

            top_count = min(
                5,
                len(BIRD_CLASS_INDICES),
            )

            top_positions = np.argsort(
                bird_probs
            )[::-1][:top_count]

            for position in top_positions:

                category_index = BIRD_CLASS_INDICES[
                    int(position)
                ]

                score = float(
                    bird_probs[position]
                )

                category_name = categories[
                    category_index
                ]

                clean_name = _clean_category_name(
                    category_name
                )

                results.append(
                    (
                        clean_name,
                        clean_name,
                        score,
                    )
                )

        # ====================================================
        # INSECT
        # ====================================================

        elif target_group == "insect":

            insect_probs = probabilities[
                INSECT_CLASS_INDICES
            ]

            # Do not force a species prediction when the
            # model has essentially no confidence.
            max_insect_score = float(
                np.max(insect_probs)
            )

            # ImageNet MobileNet is only being used as a
            # lightweight fallback. Very weak predictions
            # should be treated as "unknown".
            if max_insect_score < 0.01:
                return []

            top_count = min(
                5,
                len(INSECT_CLASS_INDICES),
            )

            top_positions = np.argsort(
                insect_probs
            )[::-1][:top_count]
            for position in top_positions:

                category_index = INSECT_CLASS_INDICES[
                    int(position)
                ]

                score = float(
                    insect_probs[position]
                )

                mapped = (
                    INSECT_ARTHROPOD_TAXONOMY_MAP.get(
                        category_index
                    )
                )

                if mapped is not None:
                    scientific_name, common_name = mapped

                else:
                    fallback_name = categories[
                        category_index
                    ]

                    scientific_name = (
                        fallback_name
                    )

                    common_name = (
                        _clean_category_name(
                            fallback_name
                        )
                    )

                results.append(
                    (
                        scientific_name,
                        common_name,
                        score,
                    )
                )

        # ====================================================
        # GENERAL
        # ====================================================

        else:

            top_count = min(
                5,
                len(probabilities),
            )

            top_indices = np.argsort(
                probabilities
            )[::-1][:top_count]

            for category_index in top_indices:

                score = float(
                    probabilities[
                        category_index
                    ]
                )

                category_name = categories[
                    int(category_index)
                ]

                clean_name = _clean_category_name(
                    category_name
                )

                results.append(
                    (
                        clean_name,
                        clean_name,
                        score,
                    )
                )

        return results

    finally:

        # Release request-level arrays.
        input_tensor = None
        output = None

        gc.collect()