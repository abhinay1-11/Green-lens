from typing import Optional

def classify_category(
    kingdom: Optional[str] = None,
    phylum: Optional[str] = None,
    class_name: Optional[str] = None,
    order: Optional[str] = None,
    family: Optional[str] = None,
    canonical_name: Optional[str] = None
) -> str:
    """
    Centralized category classification deriving category ('bird', 'plant', 'insect', 'other')
    strictly from taxonomy.
    """
    k = (kingdom or "").strip().lower()
    p = (phylum or "").strip().lower()
    c = (class_name or "").strip().lower()
    o = (order or "").strip().lower()
    f = (family or "").strip().lower()
    name = (canonical_name or "").strip().lower()

    # 1. Bird Check (Aves)
    bird_classes = {"aves"}
    bird_orders = {
        "passeriformes", "accipitriformes", "columbiformes", "strigiformes",
        "anseriformes", "falconiformes", "charadriiformes", "pelecaniformes",
        "piciformes", "psittaciformes", "galliformes", "suliformes", "coraciiformes",
        "caprimulgiformes", "gruiformes", "podicipediformes", "procellariiformes", "sphenisciformes"
    }
    bird_families = {"corvidae", "fringillidae", "passeridae", "phasianidae", "columbidae", "accipitridae", "anatidae"}

    if c in bird_classes or o in bird_orders or f in bird_families:
        return "bird"

    # 2. Insect / Arthropod Check
    insect_classes = {"insecta", "hexapoda", "entognatha", "arachnida"}
    insect_orders = {
        "hymenoptera", "lepidoptera", "coleoptera", "diptera", "hemiptera",
        "orthoptera", "odonata", "mantodea", "blattodea", "neuroptera"
    }
    if c in insect_classes or o in insect_orders or p in {"arthropoda"}:
        return "insect"

    # 3. Plant Check
    plant_kingdoms = {"plantae", "viridiplantae", "archaeplastida"}
    plant_phyla = {"tracheophyta", "magnoliophyta", "streptophyta", "bryophyta", "pinophyta", "pteridophyta"}
    plant_classes = {"magnoliopsida", "liliopsida", "pinopsida", "polypodiopsida", "equisetopsida"}

    if k in plant_kingdoms or p in plant_phyla or c in plant_classes:
        return "plant"

    # 4. Legitimate other biological organisms
    return "other"
