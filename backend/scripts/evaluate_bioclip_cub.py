import argparse
import csv
import json
import os
import re
import sys
import time
import statistics
from typing import Dict, List, Tuple, Optional
from PIL import Image

# Ensure backend root directory is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


def normalize_name(s: str) -> str:
    """
    Normalizes biological class names and common names for robust string matching:
    - Strips numeric class prefixes (e.g. '001.')
    - Replaces underscores and hyphens with spaces
    - Converts to lowercase
    - Removes non-alphanumeric characters except spaces
    - Collapses multiple whitespace characters
    """
    if not s:
        return ""
    s = re.sub(r'^\d+\.', '', s)
    s = s.replace('_', ' ').replace('-', ' ')
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s]', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def check_match(cub_class_name: str, pred_item: dict) -> bool:
    """
    Determines whether a BioCLIP prediction dictionary matches the ground-truth CUB class.
    Checks normalized equivalences across:
    1. CUB class name vs BioCLIP common name
    2. CUB class name vs BioCLIP scientific species name
    3. CUB class name vs BioCLIP genus + species epithet
    4. Token subset matching for minor naming variations (e.g. 'Cardinal' vs 'Northern Cardinal')
    """
    cub_norm = normalize_name(cub_class_name)
    if not cub_norm:
        return False

    bc_common = normalize_name(pred_item.get("common_name", ""))
    bc_species = normalize_name(pred_item.get("species", ""))
    bc_genus = normalize_name(pred_item.get("genus", ""))
    bc_epithet = normalize_name(pred_item.get("species_epithet", ""))

    # 1. Exact match on common name
    if bc_common and cub_norm == bc_common:
        return True

    # 2. Exact match on scientific species name
    if bc_species and cub_norm == bc_species:
        return True

    # 3. Exact match on genus + epithet
    full_sci = f"{bc_genus} {bc_epithet}".strip()
    if full_sci and cub_norm == normalize_name(full_sci):
        return True

    # 4. Token subset matching for compound names
    if bc_common:
        cub_tokens = set(cub_norm.split())
        bc_tokens = set(bc_common.split())

        if cub_tokens and cub_tokens.issubset(bc_tokens):
            return True
        if bc_tokens and bc_tokens.issubset(cub_tokens):
            return True

    # 5. Token subset matching for scientific name
    if bc_species:
        sci_tokens = set(bc_species.split())
        cub_tokens = set(cub_norm.split())
        if cub_tokens and cub_tokens.issubset(sci_tokens):
            return True

    return False


def load_cub_metadata(dataset_dir: str) -> Tuple[Dict[int, str], List[dict]]:
    """
    Reads CUB-200-2011 metadata files and returns:
    1. classes_map: class_id -> raw_class_name
    2. test_images: list of dicts with metadata for test split images (is_training_image == 0)
    """
    classes_path = os.path.join(dataset_dir, "classes.txt")
    images_path = os.path.join(dataset_dir, "images.txt")
    labels_path = os.path.join(dataset_dir, "image_class_labels.txt")
    split_path = os.path.join(dataset_dir, "train_test_split.txt")

    for p in [classes_path, images_path, labels_path, split_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required CUB dataset metadata file missing: {p}")

    # 1. Load classes.txt
    classes_map = {}
    with open(classes_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                classes_map[int(parts[0])] = parts[1]

    # 2. Load image_class_labels.txt
    labels_map = {}
    with open(labels_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                labels_map[int(parts[0])] = int(parts[1])

    # 3. Load train_test_split.txt (0 = test split, 1 = train split)
    split_map = {}
    with open(split_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                split_map[int(parts[0])] = int(parts[1])

    # 4. Load images.txt and assemble test set
    test_images = []
    images_root = os.path.join(dataset_dir, "images")
    with open(images_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                img_id = int(parts[0])
                rel_path = parts[1]

                is_train = split_map.get(img_id, 1)
                if is_train == 0:  # TEST SPLIT ONLY
                    class_id = labels_map.get(img_id, 0)
                    class_name = classes_map.get(class_id, "Unknown")
                    abs_path = os.path.join(images_root, rel_path.replace("/", os.sep))
                    test_images.append({
                        "image_id": img_id,
                        "rel_path": rel_path,
                        "abs_path": abs_path,
                        "class_id": class_id,
                        "class_name": class_name
                    })

    return classes_map, test_images


def evaluate(limit: Optional[int] = None, dataset_rel_dir: str = "data/datasets/CUB_200_2011"):
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    abs_dataset_dir = os.path.join(project_root, dataset_rel_dir) if not os.path.isabs(dataset_rel_dir) else dataset_rel_dir

    print("=" * 70)
    print("BIOCLIP 2 CUB-200-2011 EVALUATION")
    print("=" * 70)
    print(f"Dataset Directory: {abs_dataset_dir}")
    print(f"Limit Mode:        {limit if limit is not None else 'Full Test Split'}")

    classes_map, test_images = load_cub_metadata(abs_dataset_dir)
    total_test_available = len(test_images)
    print(f"Total Test Images Available in CUB: {total_test_available}")

    if limit is not None and limit > 0:
        test_images = test_images[:limit]
        print(f"Evaluating subset of first {len(test_images)} test images...")

    print("\n[BioCLIP] Initializing TreeOfLifeClassifier (loaded ONCE for evaluation)...")
    t0_init = time.time()
    from bioclip import TreeOfLifeClassifier, Rank
    classifier = TreeOfLifeClassifier()
    print(f"[BioCLIP] Classifier initialized in {time.time() - t0_init:.2f}s\n")

    results = []
    success_count = 0
    fail_count = 0

    top1_correct_count = 0
    top3_correct_count = 0
    top5_correct_count = 0

    latencies_ms = []
    top1_confidences = []

    t_eval_start = time.time()

    for idx, item in enumerate(test_images, start=1):
        img_id = item["image_id"]
        img_path = item["abs_path"]
        cub_class_id = item["class_id"]
        cub_class_name = item["class_name"]

        if not os.path.exists(img_path):
            print(f"[{idx}/{len(test_images)}] [MISSING FILE] {img_path}")
            fail_count += 1
            results.append({
                "image_id": img_id,
                "image_path": item["rel_path"],
                "actual_cub_class_id": cub_class_id,
                "actual_cub_class_name": cub_class_name,
                "status": "MISSING_FILE",
                "bioclip_top1_species": "",
                "bioclip_top1_common_name": "",
                "top1_confidence": 0.0,
                "top3_predictions": "",
                "top5_predictions": "",
                "is_top1_correct": False,
                "is_top3_correct": False,
                "is_top5_correct": False,
                "latency_ms": 0.0
            })
            continue

        try:
            t0 = time.time()
            pil_img = Image.open(img_path)
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")

            raw_preds = classifier.predict([pil_img], rank=Rank.SPECIES, k=5)
            elapsed_ms = (time.time() - t0) * 1000
            latencies_ms.append(elapsed_ms)
            success_count += 1

            top1 = raw_preds[0] if len(raw_preds) > 0 else {}
            top1_sci = top1.get("species", "") or f"{top1.get('genus', '')} {top1.get('species_epithet', '')}".strip()
            top1_common = top1.get("common_name", "")
            top1_conf = float(top1.get("score", 0.0))
            top1_confidences.append(top1_conf)

            is_top1 = check_match(cub_class_name, raw_preds[0]) if len(raw_preds) > 0 else False
            is_top3 = any(check_match(cub_class_name, p) for p in raw_preds[:3]) if len(raw_preds) > 0 else False
            is_top5 = any(check_match(cub_class_name, p) for p in raw_preds[:5]) if len(raw_preds) > 0 else False

            if is_top1:
                top1_correct_count += 1
            if is_top3:
                top3_correct_count += 1
            if is_top5:
                top5_correct_count += 1

            top3_str = " | ".join([f"{p.get('common_name') or p.get('species')} ({p.get('score', 0):.3f})" for p in raw_preds[:3]])
            top5_str = " | ".join([f"{p.get('common_name') or p.get('species')} ({p.get('score', 0):.3f})" for p in raw_preds[:5]])

            results.append({
                "image_id": img_id,
                "image_path": item["rel_path"],
                "actual_cub_class_id": cub_class_id,
                "actual_cub_class_name": cub_class_name,
                "status": "SUCCESS",
                "bioclip_top1_species": top1_sci,
                "bioclip_top1_common_name": top1_common,
                "top1_confidence": round(top1_conf, 4),
                "top3_predictions": top3_str,
                "top5_predictions": top5_str,
                "is_top1_correct": is_top1,
                "is_top3_correct": is_top3,
                "is_top5_correct": is_top5,
                "latency_ms": round(elapsed_ms, 1)
            })

            match_label = "TOP-1 MATCH" if is_top1 else ("TOP-3/5 MATCH" if is_top5 else "MISMATCH")
            disp_top1 = top1_common if top1_common else top1_sci
            print(f"[{idx}/{len(test_images)}] ID {img_id:4d} | Actual: {cub_class_name:<30} | Pred: {disp_top1:<25} ({top1_conf*100:5.1f}%) | [{match_label}] ({elapsed_ms:.0f}ms)")

        except Exception as exc:
            print(f"[{idx}/{len(test_images)}] [INFERENCE ERROR] ID {img_id}: {exc}")
            fail_count += 1
            results.append({
                "image_id": img_id,
                "image_path": item["rel_path"],
                "actual_cub_class_id": cub_class_id,
                "actual_cub_class_name": cub_class_name,
                "status": f"ERROR: {str(exc)}",
                "bioclip_top1_species": "",
                "bioclip_top1_common_name": "",
                "top1_confidence": 0.0,
                "top3_predictions": "",
                "top5_predictions": "",
                "is_top1_correct": False,
                "is_top3_correct": False,
                "is_top5_correct": False,
                "latency_ms": 0.0
            })

    num_eval = len(test_images)
    top1_acc = (top1_correct_count / num_eval * 100.0) if num_eval > 0 else 0.0
    top3_acc = (top3_correct_count / num_eval * 100.0) if num_eval > 0 else 0.0
    top5_acc = (top5_correct_count / num_eval * 100.0) if num_eval > 0 else 0.0

    avg_lat = sum(latencies_ms) / len(latencies_ms) if latencies_ms else 0.0
    med_lat = statistics.median(latencies_ms) if latencies_ms else 0.0
    avg_conf = sum(top1_confidences) / len(top1_confidences) if top1_confidences else 0.0

    print("\n" + "=" * 50)
    print("BIOCLIP 2 CUB-200-2011 EVALUATION")
    print("=" * 50)
    print(f"Images evaluated: {num_eval}")
    print(f"Successful:       {success_count}")
    print(f"Failed:           {fail_count}")
    print()
    print(f"Top-1 accuracy:   {top1_acc:.2f}% ({top1_correct_count}/{num_eval})")
    print(f"Top-3 accuracy:   {top3_acc:.2f}% ({top3_correct_count}/{num_eval})")
    print(f"Top-5 accuracy:   {top5_acc:.2f}% ({top5_correct_count}/{num_eval})")
    print()
    print(f"Average confidence: {avg_conf * 100:.1f}% ({avg_conf:.4f})")
    print(f"Average latency:    {avg_lat:.1f} ms")
    print(f"Median latency:     {med_lat:.1f} ms")
    print("=" * 50)

    summary = {
        "dataset": "CUB-200-2011 Test Split",
        "images_evaluated": num_eval,
        "successful_predictions": success_count,
        "failed_predictions": fail_count,
        "top1_correct_count": top1_correct_count,
        "top3_correct_count": top3_correct_count,
        "top5_correct_count": top5_correct_count,
        "top1_accuracy_percent": round(top1_acc, 2),
        "top3_accuracy_percent": round(top3_acc, 2),
        "top5_accuracy_percent": round(top5_acc, 2),
        "average_top1_confidence": round(avg_conf, 4),
        "average_latency_ms": round(avg_lat, 1),
        "median_latency_ms": round(med_lat, 1),
        "total_eval_duration_sec": round(time.time() - t_eval_start, 2)
    }

    # Save CSV
    csv_path = os.path.join(abs_dataset_dir, "bioclip_results.csv")
    fieldnames = [
        "image_id", "image_path", "actual_cub_class_id", "actual_cub_class_name",
        "status", "bioclip_top1_species", "bioclip_top1_common_name", "top1_confidence",
        "top3_predictions", "top5_predictions", "is_top1_correct", "is_top3_correct", "is_top5_correct", "latency_ms"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nDetailed CSV results saved to: {csv_path}")

    # Save JSON Summary
    json_path = os.path.join(abs_dataset_dir, "bioclip_evaluation_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Evaluation summary JSON saved to: {json_path}\n")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate BioCLIP 2 on CUB-200-2011 Test Split")
    parser.add_argument("--limit", type=int, default=None, help="Number of test images to evaluate (e.g., 20 or 100)")
    parser.add_argument("--dataset-dir", type=str, default="data/datasets/CUB_200_2011", help="Relative or absolute path to CUB-200-2011 dataset")
    args = parser.parse_args()

    evaluate(limit=args.limit, dataset_rel_dir=args.dataset_dir)