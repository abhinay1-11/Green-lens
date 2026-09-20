import sys
import os
import re

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from bioclip.predict import TreeOfLifeClassifier

print("Loading BioCLIP taxonomy table...")
clf = TreeOfLifeClassifier()
df = clf.get_label_data()

# Filter class == Aves or Aves species
aves_df = df[df["class"].str.lower() == "aves"].copy() if "class" in df.columns else df.copy()
print("Aves species in BioCLIP taxonomy table:", len(aves_df))

# Build lookup dicts by species name and common name
species_to_tax = {}
common_to_tax = {}

for idx, row in df.iterrows():
    sci = str(row.get("species", "")).strip().lower()
    common = str(row.get("common_name", "")).strip().lower()
    tax_info = {
        "kingdom": row.get("kingdom", ""),
        "class": row.get("class", ""),
        "order": row.get("order", ""),
        "family": row.get("family", ""),
        "genus": row.get("genus", ""),
        "species": row.get("species", ""),
        "common_name": row.get("common_name", "")
    }
    if sci:
        species_to_tax[sci] = tax_info
    if common:
        common_to_tax[common] = tax_info

# Test looking up a few CUB classes
test_cnames = ["Black_footed_Albatross", "Groove_billed_Ani", "Cardinal", "Gray_Catbird", "Chuck_will_Widow"]
for c in test_cnames:
    norm_c = c.replace("_", " ").lower()
    match = common_to_tax.get(norm_c) or species_to_tax.get(norm_c)
    print(f"CUB Name: {c:<25} -> Tax Match: {match['order'] if match else 'NOT FOUND'}, {match['family'] if match else 'NOT FOUND'}, {match['genus'] if match else 'NOT FOUND'}")
