import sys
import os
import re

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
dataset_dir = os.path.join(project_root, "data", "datasets", "CUB_200_2011")
classes_path = os.path.join(dataset_dir, "classes.txt")

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from bioclip.predict import TreeOfLifeClassifier

def canonical_normalize(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r'^\d+\.', '', s)
    s = s.replace("'s", "").replace("’s", "").replace("'", "").replace("’", "")
    s = s.replace('_', ' ').replace('-', ' ')
    s = s.lower()
    s = re.sub(r'\bgrey\b', 'gray', s)
    s = re.sub(r'\bleconte\b', 'le conte', s)
    s = re.sub(r'[^a-z0-9\s]', '', s)
    return re.sub(r'\s+', ' ', s).strip()

print("Loading BioCLIP label dataframe...")
clf = TreeOfLifeClassifier()
df = clf.get_label_data()

# Build normalized common name and scientific name maps to taxonomy dict
common_map = {}
species_map = {}

for idx, row in df.iterrows():
    c_norm = canonical_normalize(row.get("common_name", ""))
    s_norm = canonical_normalize(row.get("species", ""))
    tax = {
        "kingdom": str(row.get("kingdom", "")),
        "class": str(row.get("class", "")),
        "order": str(row.get("order", "")),
        "family": str(row.get("family", "")),
        "genus": str(row.get("genus", "")),
        "species": str(row.get("species", "")),
        "common_name": str(row.get("common_name", ""))
    }
    if c_norm and c_norm not in common_map:
        common_map[c_norm] = tax
    if s_norm and s_norm not in species_map:
        species_map[s_norm] = tax

# Manual taxonomy overrides for CUB class names that use archaic/regional names or dataset typos
CUB_TAXONOMY_OVERRIDES = {
    "004.groove billed ani": "crotophaga sulcirostris",
    "017.cardinal": "cardinalis cardinalis",
    "018.spotted catbird": "ailuroedus melanotis",
    "019.gray catbird": "dumetella carolinensis",
    "022.chuck will widow": "antrostomus carolinensis",
    "070.green violetear": "colibri thalassinus",
    "071.long tailed jaeger": "stercorarius longicaudus",
    "083.white breasted kingfisher": "halcyon smyrnensis",
    "104.american pipit": "anthus rubescens",
    "126.nelson sharp tailed sparrow": "ammospiza nelsoni",
    "141.artic tern": "sterna paradisaea",
    "171.myrtle warbler": "setophaga coronata",
    "175.pine warbler": "setophaga pinus",
    "188.pileated woodpecker": "dryocopus pileatus",
    "193.bewick wren": "thryomanes bewickii",
}

print("Testing lookup for all 200 CUB classes...")
found_count = 0
missing = []

with open(classes_path, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 2:
            cid = parts[0]
            raw_cname = parts[1]
            norm_c = canonical_normalize(raw_cname)

            tax = common_map.get(norm_c) or species_map.get(norm_c)

            if not tax and norm_c in CUB_TAXONOMY_OVERRIDES:
                override_sci = canonical_normalize(CUB_TAXONOMY_OVERRIDES[norm_c])
                tax = species_map.get(override_sci)

            if tax:
                found_count += 1
            else:
                missing.append(raw_cname)

print(f"Mapped {found_count} / 200 CUB species to BioCLIP taxonomy!")
if missing:
    print(f"Missing {len(missing)} species:", missing[:10])
