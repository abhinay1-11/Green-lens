import os
import sys
import time
import json
import csv
import statistics
from PIL import Image

# Ensure backend root on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.identification.insect import InsectProvider

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/test_images/insects"))
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

GROUND_TRUTH = {
    "bee_sample.jpg": ("Apis mellifera", "Western Honey Bee"),
    "butterfly_monarch.jpg": ("Danaus plexippus", "Monarch Butterfly"),
    "dragonfly_blue.jpg": ("Anax junius", "Green Darner Dragonfly")
}

def run_benchmark():
    print("==========================================================")
    print("INSECT SPECIES CLASSIFIER EVALUATION BENCHMARK")
    print("==========================================================")

    provider = InsectProvider()

    test_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(('.jpg', '.png', '.webp'))]

    results = []
    latencies = []
    top1_hits = 0
    top3_hits = 0
    top5_hits = 0
    successes = 0
    failures = 0

    for fname in sorted(test_files):
        fpath = os.path.join(DATA_DIR, fname)
        gt_sci, gt_com = GROUND_TRUTH.get(fname, ("Unknown", "Unknown"))

        try:
            with open(fpath, "rb") as f:
                img_bytes = f.read()

            t0 = time.time()
            res = provider.identify([{"file_bytes": img_bytes, "filename": fname}], category="insect")
            latency_ms = round((time.time() - t0) * 1000, 2)
            latencies.append(latency_ms)

            if not res.success or not res.predictions:
                failures += 1
                results.append({
                    "image": fname,
                    "ground_truth": gt_com,
                    "prediction": "None",
                    "confidence": "0.0%",
                    "top_3": "None",
                    "top_5": "None",
                    "correct": False,
                    "latency_ms": latency_ms
                })
                print(f"  [FAILED] {fname} ({latency_ms}ms)")
                continue

            successes += 1
            preds = res.predictions
            top1 = preds[0]
            top3_names = [p.common_names[0] if p.common_names else p.scientific_name for p in preds[:3]]
            top5_names = [p.common_names[0] if p.common_names else p.scientific_name for p in preds[:5]]

            # Check correctness against ground truth (order/family/species/common match)
            gt_keywords = [gt_sci.lower(), gt_com.lower()] + gt_com.lower().split()
            is_top1 = any(kw in top1.scientific_name.lower() or any(kw in c.lower() for c in top1.common_names) for kw in gt_keywords if len(kw) > 3)
            is_top3 = any(any(kw in t3.lower() for kw in gt_keywords if len(kw) > 3) for t3 in top3_names)
            is_top5 = any(any(kw in t5.lower() for kw in gt_keywords if len(kw) > 3) for t5 in top5_names)

            if is_top1: top1_hits += 1
            if is_top3: top3_hits += 1
            if is_top5: top5_hits += 1

            results.append({
                "image": fname,
                "ground_truth": f"{gt_com} ({gt_sci})",
                "prediction": f"{top1.common_names[0] if top1.common_names else top1.scientific_name} ({top1.scientific_name})",
                "confidence": f"{top1.confidence * 100:.1f}%",
                "top_3": "; ".join(top3_names),
                "top_5": "; ".join(top5_names),
                "correct": is_top1 or is_top3,
                "latency_ms": latency_ms
            })
            print(f"  [PROCESSED] {fname} -> Top: {top1.scientific_name} ({top1.confidence*100:.1f}%) [{latency_ms}ms]")

        except Exception as err:
            failures += 1
            print(f"  [ERROR] {fname}: {err}")

    # Write CSV artifact
    csv_path = os.path.join(OUTPUT_DIR, "insect_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "ground_truth", "prediction", "confidence", "top_3", "top_5", "correct", "latency_ms"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\nWritten: {csv_path}")

    # Write Summary JSON artifact
    total_imgs = len(test_files)
    summary_data = {
        "number_of_images": total_imgs,
        "number_of_species_classes": 35,
        "successful_predictions": successes,
        "failed_predictions": failures,
        "top1_accuracy": round((top1_hits / max(1, total_imgs)) * 100, 1),
        "top3_accuracy": round((top3_hits / max(1, total_imgs)) * 100, 1),
        "top5_accuracy": round((top5_hits / max(1, total_imgs)) * 100, 1),
        "average_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0.0,
        "median_latency_ms": round(statistics.median(latencies), 2) if latencies else 0.0
    }
    json_path = os.path.join(OUTPUT_DIR, "insect_evaluation_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Written: {json_path}")

    print("\n==========================================================")
    print("BENCHMARK SUMMARY:")
    print(json.dumps(summary_data, indent=2))
    print("==========================================================")

if __name__ == "__main__":
    run_benchmark()
