import io
from typing import List, Tuple

from PIL import Image


_MODEL = None
_TRANSFORMS = None
_CATEGORIES = None
_TORCH = None


# Exact ImageNet 1k class indices for Birds (Aves)
BIRD_CLASS_INDICES = list(
    set(range(8, 25))
    | set(range(80, 101))
    | set(range(127, 147))
)


# Exact ImageNet 1k taxonomy mapping for Insects & Arthropods
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

INSECT_CLASS_INDICES = sorted(INSECT_ARTHROPOD_TAXONOMY_MAP.keys())


# Maximum image dimension before model preprocessing.
# 384 is more than enough because the ResNet transform ultimately
# resizes/crops to 224x224.
MAX_IMAGE_SIZE = 384


def _load_model():
    """
    Lazily load PyTorch and ResNet50.

    IMPORTANT:
    torch and torchvision are intentionally imported here instead
    of at module startup. This keeps /health and other lightweight
    requests from immediately paying the full PyTorch import cost.
    """
    global _MODEL, _TRANSFORMS, _CATEGORIES, _TORCH

    if _MODEL is None:
        print("[LOCAL_MODEL] Loading PyTorch ResNet50 lazily...")

        import torch
        import torchvision.models as models

        _TORCH = torch

        weights = models.ResNet50_Weights.DEFAULT

        _MODEL = models.resnet50(weights=weights)
        _MODEL.eval()

        _TRANSFORMS = weights.transforms()
        _CATEGORIES = weights.meta["categories"]

        print("[LOCAL_MODEL] ResNet50 loaded successfully.")

    return _MODEL, _TRANSFORMS, _CATEGORIES, _TORCH


def _prepare_image(image_bytes: bytes) -> Image.Image:
    """
    Safely prepare an uploaded image while minimizing memory usage.

    The critical optimization is resizing BEFORE converting to RGB.
    This prevents a large 12MP/48MP camera image from remaining as
    a huge RGB bitmap in memory.
    """

    image_stream = io.BytesIO(image_bytes)

    try:
        img = Image.open(image_stream)

        # Fix EXIF orientation if present.
        # Imported lazily because it is only needed for inference.
        from PIL import ImageOps

        img = ImageOps.exif_transpose(img)

        # Downsample BEFORE RGB conversion.
        #
        # Example:
        # 4000x3000 -> approximately 384x288
        # 8000x6000 -> approximately 384x288
        #
        # This dramatically reduces transient memory usage.
        img.thumbnail(
            (MAX_IMAGE_SIZE, MAX_IMAGE_SIZE),
            Image.Resampling.LANCZOS,
        )

        # Only now create the RGB image.
        img = img.convert("RGB")

        return img

    finally:
        image_stream.close()


def run_local_species_classifier(
    image_bytes: bytes,
    target_group: str = "bird",
) -> List[Tuple[str, str, float]]:
    """
    Executes local species classification using PyTorch ResNet50.

    target_group:
        - "bird"
        - "insect"
        - "general"

    Returns:
        List of:
        (scientific_name, common_name, confidence)
    """

    model, transform, categories, torch = _load_model()

    img = None
    tensor = None
    logits = None
    probabilities = None

    try:
        # ---------------------------------------------------------
        # 1. Memory-safe image preparation
        # ---------------------------------------------------------
        img = _prepare_image(image_bytes)

        # ---------------------------------------------------------
        # 2. Convert to model tensor
        # ---------------------------------------------------------
        tensor = transform(img).unsqueeze(0)

        # ---------------------------------------------------------
        # 3. Memory-efficient inference
        # ---------------------------------------------------------
        with torch.inference_mode():
            logits = model(tensor)[0]

        results: List[Tuple[str, str, float]] = []

        # =========================================================
        # BIRD
        # =========================================================
        if target_group == "bird":

            bird_indices = BIRD_CLASS_INDICES

            bird_logits = logits[bird_indices]

            bird_sub_probs = torch.nn.functional.softmax(
                bird_logits,
                dim=0,
            )

            topk_probs, topk_sub_idx = torch.topk(
                bird_sub_probs,
                min(5, len(bird_indices)),
            )

            for i in range(topk_probs.size(0)):

                cat_idx = bird_indices[
                    topk_sub_idx[i].item()
                ]

                cat_name = categories[cat_idx]

                score = float(
                    topk_probs[i].item()
                )

                clean_name = (
                    cat_name
                    .replace("_", " ")
                    .title()
                )

                results.append(
                    (
                        clean_name,
                        clean_name,
                        score,
                    )
                )

            return results

        # =========================================================
        # INSECT
        # =========================================================
        elif target_group == "insect":

            insect_indices = INSECT_CLASS_INDICES

            insect_logits = logits[insect_indices]

            insect_sub_probs = torch.nn.functional.softmax(
                insect_logits,
                dim=0,
            )

            topk_probs, topk_sub_idx = torch.topk(
                insect_sub_probs,
                min(5, len(insect_indices)),
            )

            for i in range(topk_probs.size(0)):

                cat_idx = insect_indices[
                    topk_sub_idx[i].item()
                ]

                score = float(
                    topk_probs[i].item()
                )

                sci_name, com_name = (
                    INSECT_ARTHROPOD_TAXONOMY_MAP.get(
                        cat_idx,
                        (
                            categories[cat_idx],
                            categories[cat_idx]
                            .replace("_", " ")
                            .title(),
                        ),
                    )
                )

                results.append(
                    (
                        sci_name,
                        com_name,
                        score,
                    )
                )

            return results

        # =========================================================
        # GENERAL
        # =========================================================
        else:

            probabilities = torch.nn.functional.softmax(
                logits,
                dim=0,
            )

            top5_prob, top5_catid = torch.topk(
                probabilities,
                5,
            )

            for i in range(top5_prob.size(0)):

                cat_idx = top5_catid[i].item()

                cat_name = categories[cat_idx]

                score = float(
                    top5_prob[i].item()
                )

                clean_name = (
                    cat_name
                    .replace("_", " ")
                    .title()
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
        # ---------------------------------------------------------
        # Explicitly release request-specific objects.
        # The model itself remains cached intentionally.
        # ---------------------------------------------------------

        del img
        del tensor
        del logits

        if probabilities is not None:
            del probabilities