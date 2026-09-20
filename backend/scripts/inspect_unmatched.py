import csv
import os
import re
from collections import Counter

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
csv_path = os.path.join(project_root, "data", "datasets", "CUB_200_2011", "bioclip_results.csv")

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

with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

unmatched_pairs = []
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

    is_canonical_match = (norm_cub == norm_common) or (norm_cub == norm_sci)
    if not is_canonical_match:
        unmatched_pairs.append((cub_name, bc_common, bc_sci))

pair_counts = Counter(unmatched_pairs)
print("Top 30 Unmatched Pairs:")
for (cub, common, sci), count in pair_counts.most_common(30):
    print(f"Count: {count:2d} | CUB: {cub:<32} | BioCLIP Common: {common:<30} | BioCLIP Sci: {sci}")
