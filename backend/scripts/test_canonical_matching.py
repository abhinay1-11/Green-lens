import csv
import os
import re

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
csv_path = os.path.join(project_root, "data", "datasets", "CUB_200_2011", "bioclip_results.csv")

def canonical_normalize(s: str) -> str:
    if not s:
        return ""
    # Strip numeric prefix e.g. "093."
    s = re.sub(r'^\d+\.', '', s)
    # Replace possessives "'s", "’s", "'", "’"
    s = s.replace("'s", "").replace("’s", "").replace("'", "").replace("’", "")
    # Standardize hyphens and underscores to space
    s = s.replace('_', ' ').replace('-', ' ')
    # Lowercase
    s = s.lower()
    # Normalize regional spelling "grey" -> "gray"
    s = re.sub(r'\bgrey\b', 'gray', s)
    # Normalize "leconte" -> "le conte"
    s = re.sub(r'\bleconte\b', 'le conte', s)
    # Remove non-alphanumeric chars except space
    s = re.sub(r'[^a-z0-9\s]', '', s)
    # Collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    return s

with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

total = len(rows)
raw_correct = sum(1 for r in rows if r["is_top1_correct"].lower() == "true")
naming_variants_count = 0
genuine_mismatches_count = 0

for r in rows:
    raw_match = (r["is_top1_correct"].lower() == "true")
    if raw_match:
        continue
    
    cub_name = r["actual_cub_class_name"]
    bc_common = r["bioclip_top1_common_name"]
    bc_sci = r["bioclip_top1_species"]

    norm_cub = canonical_normalize(cub_name)
    norm_common = canonical_normalize(bc_common)
    norm_sci = canonical_normalize(bc_sci)

    # Check canonical match
    is_canonical_match = (norm_cub == norm_common) or (norm_cub == norm_sci)
    
    if is_canonical_match:
        naming_variants_count += 1
    else:
        genuine_mismatches_count += 1

print(f"Total Test Images:                   {total}")
print(f"Raw String Matches (EXACT):          {raw_correct} ({raw_correct/total*100:.2f}%)")
print(f"Naming Variant Matches (RESOLVED):   {naming_variants_count} ({naming_variants_count/total*100:.2f}%)")
print(f"Canonical Top-1 Correct Total:       {raw_correct + naming_variants_count} ({(raw_correct + naming_variants_count)/total*100:.2f}%)")
print(f"Genuine Visual Mismatches Remaining: {genuine_mismatches_count} ({genuine_mismatches_count/total*100:.2f}%)")
