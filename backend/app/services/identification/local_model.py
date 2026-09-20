import io
from typing import List, Tuple
from PIL import Image
import torch
import torchvision.models as models

_MODEL = None
_TRANSFORMS = None
_CATEGORIES = None

# Exact ImageNet 1k class indices for Birds (Aves): 58 bird species classes
BIRD_CLASS_INDICES = list(set(range(8, 25)) | set(range(80, 101)) | set(range(127, 147)))

# Exact ImageNet 1k taxonomy mapping for Insects & Arthropods (35 species classes)
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

def _load_model():
    global _MODEL, _TRANSFORMS, _CATEGORIES
    if _MODEL is None:
        weights = models.ResNet50_Weights.DEFAULT
        _MODEL = models.resnet50(weights=weights).eval()
        _TRANSFORMS = weights.transforms()
        _CATEGORIES = weights.meta["categories"]
    return _MODEL, _TRANSFORMS, _CATEGORIES

def run_local_species_classifier(image_bytes: bytes, target_group: str = "bird") -> List[Tuple[str, str, float]]:
    """
    Executes fast local species classification using PyTorch ResNet50 model.
    Extracts top taxonomic predictions for target_group ('bird' or 'insect' or 'general').
    Returns: List of (scientific_name, common_name, confidence_float)
    """
    model, transform, categories = _load_model()
    
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = transform(img).unsqueeze(0)
    
    with torch.no_grad():
        logits = model(tensor)[0]
        probabilities = torch.nn.functional.softmax(logits, dim=0)

    results = []

    if target_group == "bird":
        # Sliced logits softmax re-normalization for bird classes
        bird_indices = BIRD_CLASS_INDICES
        bird_logits = logits[bird_indices]
        bird_sub_probs = torch.nn.functional.softmax(bird_logits, dim=0)
        
        topk_probs, topk_sub_idx = torch.topk(bird_sub_probs, min(5, len(bird_indices)))
        for i in range(topk_probs.size(0)):
            cat_idx = bird_indices[topk_sub_idx[i].item()]
            cat_name = categories[cat_idx]
            score = topk_probs[i].item()
            clean_name = cat_name.replace("_", " ").title()
            results.append((clean_name, clean_name, score))

    elif target_group == "insect":
        # Sliced logits softmax re-normalization & binomial taxonomy mapping for insect/arthropod classes
        insect_indices = INSECT_CLASS_INDICES
        insect_logits = logits[insect_indices]
        insect_sub_probs = torch.nn.functional.softmax(insect_logits, dim=0)
        
        topk_probs, topk_sub_idx = torch.topk(insect_sub_probs, min(5, len(insect_indices)))
        for i in range(topk_probs.size(0)):
            cat_idx = insect_indices[topk_sub_idx[i].item()]
            score = topk_probs[i].item()
            sci_name, com_name = INSECT_ARTHROPOD_TAXONOMY_MAP.get(cat_idx, (categories[cat_idx], categories[cat_idx].replace("_", " ").title()))
            results.append((sci_name, com_name, score))

    else:
        # General top predictions
        top5_prob, top5_catid = torch.topk(probabilities, 5)
        for i in range(top5_prob.size(0)):
            cat_name = categories[top5_catid[i]]
            score = top5_prob[i].item()
            clean_name = cat_name.replace("_", " ").title()
            results.append((clean_name, clean_name, score))

    return results
