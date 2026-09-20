import csv
import json
import os
import re

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
dataset_dir = os.path.join(project_root, "data", "datasets", "CUB_200_2011")
analysis_dir = os.path.join(dataset_dir, "analysis")
os.makedirs(analysis_dir, exist_ok=True)

csv_path = os.path.join(dataset_dir, "bioclip_results.csv")
classes_path = os.path.join(dataset_dir, "classes.txt")

# CUB class taxonomy synonym map to handle known biological synonyms & typos in CUB
# e.g. "Artic" typo in CUB -> "Arctic", "Jaeger" -> "Skua", "Pipit" -> "Anthus rubescens", etc.
TAXONOMY_SYNONYMS = {
    "artic tern": ["arctic tern", "sterna paradisaea"],
    "long tailed jaeger": ["long tailed skua", "stercorarius longicaudus"],
    "american pipit": ["buff bellied pipit", "anthus rubescens"],
    "myrtle warbler": ["yellow rumped warbler", "setophaga coronata"],
    "bank swallow": ["sand martin", "collared sand martin", "riparia riparia"],
    "nelson sharp tailed sparrow": ["nelsons sparrow", "nelson sparrow", "ammospiza nelsoni"],
}

def canonical_normalize(name: str) -> str:
    if not name:
        return ""
    # Strip numeric CUB prefix e.g. "093."
    s = re.sub(r'^\d+\.', '', name)
    # Strip possessive apostrophes ('s, ’s, ', ’)
    s = s.replace("'s", "").replace("’s", "").replace("'", "").replace("’", "")
    # Replace hyphens and underscores with spaces
    s = s.replace('_', ' ').replace('-', ' ')
    # Lowercase
    s = s.lower()
    # Normalize regional spellings
    s = re.sub(r'\bgrey\b', 'gray', s)
    s = re.sub(r'\bleconte\b', 'le conte', s)
    # Remove non-alphanumeric chars except space
    s = re.sub(r'[^a-z0-9\s]', '', s)
    # Collapse whitespace
    return re.sub(r'\s+', ' ', s).strip()

def check_canonical_match(cub_raw_name: str, pred_name_str: str, pred_sci_str: str = "") -> bool:
    norm_cub = canonical_normalize(cub_raw_name)
    norm_pred_name = canonical_normalize(pred_name_str)
    norm_pred_sci = canonical_normalize(pred_sci_str)

    if not norm_cub:
        return False

    # 1. Direct normalized match
    if norm_pred_name and norm_cub == norm_pred_name:
        return True
    if norm_pred_sci and norm_cub == norm_pred_sci:
        return True

    # 2. Known biological synonym / typo lookup match
    synonyms = TAXONOMY_SYNONYMS.get(norm_cub, [])
    for syn in synonyms:
        norm_syn = canonical_normalize(syn)
        if norm_pred_name == norm_syn or norm_pred_sci == norm_syn:
            return True

    return False

def parse_predictions_string(pred_str: str) -> list:
    """Parses top3_predictions or top5_predictions string: 'Name (score) | Name (score)'"""
    candidates = []
    if not pred_str:
        return candidates
    parts = pred_str.split(" | ")
    for part in parts:
        # Extract name before score e.g. "Black-footed Albatross (0.900)" -> "Black-footed Albatross"
        m = re.match(r'^(.*?)(?:\s*\([\d\.]+\))?$', part.strip())
        if m:
            candidates.append(m.group(1).strip())
    return candidates

print("Loading bioclip_results.csv...")
rows = []
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

total_images = len(rows)
print(f"Total rows loaded: {total_images}")

canonical_results = []
raw_top1_correct = 0
canonical_top1_correct = 0

raw_top3_correct = 0
canonical_top3_correct = 0

raw_top5_correct = 0
canonical_top5_correct = 0

exact_count = 0
naming_variant_count = 0
genuine_mismatch_count = 0

for r in rows:
    img_id = int(r["image_id"])
    cub_name = r["actual_cub_class_name"]
    bioclip_top1_sci = r["bioclip_top1_species"]
    bioclip_top1_common = r["bioclip_top1_common_name"]
    raw_top1_match = str(r["is_top1_correct"]).lower() == "true"
    raw_top3_match = str(r["is_top3_correct"]).lower() == "true"
    raw_top5_match = str(r["is_top5_correct"]).lower() == "true"

    if raw_top1_match:
        raw_top1_correct += 1

    if raw_top3_match:
        raw_top3_correct += 1

    if raw_top5_match:
        raw_top5_correct += 1

    norm_cub = canonical_normalize(cub_name)
    raw_pred_top1 = bioclip_top1_common or bioclip_top1_sci
    norm_pred_top1 = canonical_normalize(raw_pred_top1)

    # Classify match type
    is_top1_canon = check_canonical_match(cub_name, bioclip_top1_common, bioclip_top1_sci)

    if raw_top1_match:
        match_type = "EXACT"
        exact_count += 1
        canonical_top1_correct += 1
    elif is_top1_canon:
        match_type = "NAMING_VARIANT"
        naming_variant_count += 1
        canonical_top1_correct += 1
    else:
        match_type = "GENUINE_MISMATCH"
        genuine_mismatch_count += 1

    # Evaluate Top-3 Canonical Match
    top3_candidates = parse_predictions_string(r["top3_predictions"])
    is_top3_canon = raw_top3_match or any(check_canonical_match(cub_name, cand) for cand in top3_candidates)
    if is_top3_canon:
        canonical_top3_correct += 1

    # Evaluate Top-5 Canonical Match
    top5_candidates = parse_predictions_string(r["top5_predictions"])
    is_top5_canon = raw_top5_match or any(check_canonical_match(cub_name, cand) for cand in top5_candidates)
    if is_top5_canon:
        canonical_top5_correct += 1

    canonical_results.append({
        "image_id": img_id,
        "image_path": r["image_path"],
        "ground_truth": cub_name,
        "raw_prediction": raw_pred_top1,
        "normalized_ground_truth": norm_cub,
        "normalized_prediction": norm_pred_top1,
        "bioclip_scientific_name": bioclip_top1_sci,
        "top1_confidence": float(r["top1_confidence"]) if r["top1_confidence"] else 0.0,
        "match_type": match_type,
        "raw_top1_correct": raw_top1_match,
        "canonical_top1_correct": is_top1_canon or raw_top1_match,
        "raw_top3_correct": raw_top3_match,
        "canonical_top3_correct": is_top3_canon,
        "raw_top5_correct": raw_top5_match,
        "canonical_top5_correct": is_top5_canon,
        "latency_ms": float(r["latency_ms"]) if r["latency_ms"] else 0.0
    })

# Output CSV
csv_out_path = os.path.join(analysis_dir, "canonical_species_results.csv")
with open(csv_out_path, "w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "image_id", "image_path", "ground_truth", "raw_prediction",
        "normalized_ground_truth", "normalized_prediction", "bioclip_scientific_name",
        "top1_confidence", "match_type", "raw_top1_correct", "canonical_top1_correct",
        "raw_top3_correct", "canonical_top3_correct", "raw_top5_correct", "canonical_top5_correct", "latency_ms"
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(canonical_results)
print(f"Saved {csv_out_path}")

# Summary JSON
summary_json = {
    "total_test_images": total_images,
    "raw_metrics": {
        "raw_top1_correct": raw_top1_correct,
        "raw_top1_accuracy_percent": round(raw_top1_correct / total_images * 100.0, 2),
        "raw_top3_correct": raw_top3_correct,
        "raw_top3_accuracy_percent": round(raw_top3_correct / total_images * 100.0, 2),
        "raw_top5_correct": raw_top5_correct,
        "raw_top5_accuracy_percent": round(raw_top5_correct / total_images * 100.0, 2),
        "raw_mismatches_total": total_images - raw_top1_correct
    },
    "canonical_metrics": {
        "exact_matches": exact_count,
        "naming_variant_matches": naming_variant_count,
        "genuine_mismatches": genuine_mismatch_count,
        "canonical_top1_correct": canonical_top1_correct,
        "canonical_top1_accuracy_percent": round(canonical_top1_correct / total_images * 100.0, 2),
        "canonical_top3_correct": canonical_top3_correct,
        "canonical_top3_accuracy_percent": round(canonical_top3_correct / total_images * 100.0, 2),
        "canonical_top5_correct": canonical_top5_correct,
        "canonical_top5_accuracy_percent": round(canonical_top5_correct / total_images * 100.0, 2)
    },
    "mismatch_resolution": {
        "raw_mismatches_resolved_by_naming": naming_variant_count,
        "raw_mismatches_resolved_percent": round(naming_variant_count / (total_images - raw_top1_correct) * 100.0, 2),
        "remaining_genuine_species_errors": genuine_mismatch_count,
        "remaining_genuine_species_error_percent": round(genuine_mismatch_count / total_images * 100.0, 2)
    }
}

json_out_path = os.path.join(analysis_dir, "canonical_accuracy_summary.json")
with open(json_out_path, "w", encoding="utf-8") as f:
    json.dump(summary_json, f, indent=2)
print(f"Saved {json_out_path}")

print("\n" + "=" * 50)
print("CANONICAL BENCHMARK EVALUATION SUMMARY")
print("=" * 50)
print(json.dumps(summary_json, indent=2))
