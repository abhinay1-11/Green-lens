import csv
import json
import math
import os
from collections import defaultdict

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
analysis_dir = os.path.join(project_root, "data", "datasets", "CUB_200_2011", "analysis")
csv_path = os.path.join(project_root, "data", "datasets", "CUB_200_2011", "bioclip_results.csv")

os.makedirs(analysis_dir, exist_ok=True)

print("Loading bioclip_results.csv...")
data = []
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["image_id"] = int(row["image_id"])
        row["actual_cub_class_id"] = int(row["actual_cub_class_id"])
        row["top1_confidence"] = float(row["top1_confidence"]) if row["top1_confidence"] else 0.0
        row["is_top1_correct"] = str(row["is_top1_correct"]).lower() == "true"
        row["is_top3_correct"] = str(row["is_top3_correct"]).lower() == "true"
        row["is_top5_correct"] = str(row["is_top5_correct"]).lower() == "true"
        row["latency_ms"] = float(row["latency_ms"]) if row["latency_ms"] else 0.0
        data.append(row)

total = len(data)
print(f"Total test images loaded: {total}")

# 1. Per-Species Top-1 Accuracy
species_stats = defaultdict(lambda: {"class_id": 0, "total": 0, "correct": 0, "confidences": []})
for row in data:
    cname = row["actual_cub_class_name"]
    species_stats[cname]["class_id"] = row["actual_cub_class_id"]
    species_stats[cname]["total"] += 1
    species_stats[cname]["confidences"].append(row["top1_confidence"])
    if row["is_top1_correct"]:
        species_stats[cname]["correct"] += 1

species_accuracy_rows = []
for cname, stats in species_stats.items():
    tot = stats["total"]
    corr = stats["correct"]
    inc = tot - corr
    acc = (corr / tot * 100.0) if tot > 0 else 0.0
    avg_conf = sum(stats["confidences"]) / len(stats["confidences"]) if stats["confidences"] else 0.0
    species_accuracy_rows.append({
        "actual_cub_class_id": stats["class_id"],
        "actual_cub_class_name": cname,
        "total_images": tot,
        "correct_count": corr,
        "incorrect_count": inc,
        "accuracy_percent": round(acc, 2),
        "average_confidence": round(avg_conf, 4)
    })

species_accuracy_rows.sort(key=lambda x: x["actual_cub_class_id"])

species_csv_path = os.path.join(analysis_dir, "species_accuracy.csv")
with open(species_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "actual_cub_class_id", "actual_cub_class_name", "total_images",
        "correct_count", "incorrect_count", "accuracy_percent", "average_confidence"
    ])
    writer.writeheader()
    writer.writerows(species_accuracy_rows)

print(f"Wrote {species_csv_path}")

# 2. Confusion Pairs
confusion_pairs = defaultdict(lambda: {"count": 0, "confidences": []})
for row in data:
    if not row["is_top1_correct"]:
        act = row["actual_cub_class_name"]
        pred_name = row["bioclip_top1_common_name"] or row["bioclip_top1_species"] or "Unknown"
        pair_key = (act, pred_name)
        confusion_pairs[pair_key]["count"] += 1
        confusion_pairs[pair_key]["confidences"].append(row["top1_confidence"])

confusion_rows = []
for (act, pred), stats in confusion_pairs.items():
    avg_c = sum(stats["confidences"]) / len(stats["confidences"])
    confusion_rows.append({
        "actual_cub_class_name": act,
        "predicted_species": pred,
        "count": stats["count"],
        "average_confidence": round(avg_c, 4)
    })

confusion_rows.sort(key=lambda x: (x["count"], x["average_confidence"]), reverse=True)

confusion_csv_path = os.path.join(analysis_dir, "confusion_pairs.csv")
with open(confusion_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "actual_cub_class_name", "predicted_species", "count", "average_confidence"
    ])
    writer.writeheader()
    writer.writerows(confusion_rows)

print(f"Wrote {confusion_csv_path}")

# 3. Confidence Calibration
bins = [
    ("0-10%", 0.0, 0.10),
    ("10-20%", 0.10, 0.20),
    ("20-30%", 0.20, 0.30),
    ("30-40%", 0.30, 0.40),
    ("40-50%", 0.40, 0.50),
    ("50-60%", 0.50, 0.60),
    ("60-70%", 0.60, 0.70),
    ("70-80%", 0.70, 0.80),
    ("80-90%", 0.80, 0.90),
    ("90-100%", 0.90, 1.00001),
]

calibration_rows = []
for label, low, high in bins:
    bin_items = [r for r in data if low <= r["top1_confidence"] < high or (high > 1.0 and r["top1_confidence"] == 1.0)]
    tot = len(bin_items)
    corr = sum(1 for r in bin_items if r["is_top1_correct"])
    inc = tot - corr
    acc = (corr / tot * 100.0) if tot > 0 else 0.0
    avg_c = (sum(r["top1_confidence"] for r in bin_items) / tot) if tot > 0 else 0.0

    calibration_rows.append({
        "bin_range": label,
        "total_predictions": tot,
        "correct_count": corr,
        "incorrect_count": inc,
        "accuracy_percent": round(acc, 2),
        "average_confidence": round(avg_c, 4)
    })

calibration_csv_path = os.path.join(analysis_dir, "confidence_analysis.csv")
with open(calibration_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "bin_range", "total_predictions", "correct_count", "incorrect_count",
        "accuracy_percent", "average_confidence"
    ])
    writer.writeheader()
    writer.writerows(calibration_rows)

print(f"Wrote {calibration_csv_path}")

# 4. Latency Analysis
latencies = sorted([r["latency_ms"] for r in data])
avg_lat_all = sum(latencies) / len(latencies) if latencies else 0.0

def percentile(arr, pct):
    if not arr:
        return 0.0
    k = (len(arr) - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return arr[int(k)]
    return arr[int(f)] * (c - k) + arr[int(c)] * (k - f)

p50_lat = percentile(latencies, 50)
p95_lat = percentile(latencies, 95)
p99_lat = percentile(latencies, 99)

trim_count_1pct = max(1, int(len(latencies) * 0.01))
latencies_no_outliers_1pct = latencies[:-trim_count_1pct]
avg_lat_no_outliers_1pct = sum(latencies_no_outliers_1pct) / len(latencies_no_outliers_1pct)

trim_count_5pct = max(1, int(len(latencies) * 0.05))
latencies_no_outliers_5pct = latencies[:-trim_count_5pct]
avg_lat_no_outliers_5pct = sum(latencies_no_outliers_5pct) / len(latencies_no_outliers_5pct)

slow_gt_5s = sum(1 for l in latencies if l > 5000)
slow_gt_10s = sum(1 for l in latencies if l > 10000)
slow_gt_30s = sum(1 for l in latencies if l > 30000)
max_lat = max(latencies) if latencies else 0.0

latency_summary = {
    "total_predictions": len(latencies),
    "average_latency_ms_overall": round(avg_lat_all, 1),
    "median_latency_ms": round(p50_lat, 1),
    "p95_latency_ms": round(p95_lat, 1),
    "p99_latency_ms": round(p99_lat, 1),
    "max_latency_ms": round(max_lat, 1),
    "average_latency_excluding_top_1pct_outliers_ms": round(avg_lat_no_outliers_1pct, 1),
    "average_latency_excluding_top_5pct_outliers_ms": round(avg_lat_no_outliers_5pct, 1),
    "slow_predictions_gt_5000ms": slow_gt_5s,
    "slow_predictions_gt_10000ms": slow_gt_10s,
    "slow_predictions_gt_30000ms": slow_gt_30s
}

latency_json_path = os.path.join(analysis_dir, "latency_analysis.json")
with open(latency_json_path, "w", encoding="utf-8") as f:
    json.dump(latency_summary, f, indent=2)

print(f"Wrote {latency_json_path}")

# Print summary metrics to console for report generation
top1_failures = [r for r in data if not r["is_top1_correct"]]
top3_recovered = [r for r in top1_failures if r["is_top3_correct"]]
top5_recovered = [r for r in top1_failures if r["is_top5_correct"]]
not_in_top5 = [r for r in top1_failures if not r["is_top5_correct"]]

print("\n==========================================")
print("SUMMARY STATS FOR REPORT GENERATION")
print("==========================================")
print(f"Total Test Images: {total}")
print(f"Top-1 Failures: {len(top1_failures)} ({len(top1_failures)/total*100:.2f}%)")
print(f"Top-3 Recovered: {len(top3_recovered)} ({len(top3_recovered)/len(top1_failures)*100:.2f}% of failures, {len(top3_recovered)/total*100:.2f}% of total)")
print(f"Top-5 Recovered: {len(top5_recovered)} ({len(top5_recovered)/len(top1_failures)*100:.2f}% of failures, {len(top5_recovered)/total*100:.2f}% of total)")
print(f"Not in Top-5: {len(not_in_top5)} ({len(not_in_top5)/len(top1_failures)*100:.2f}% of failures, {len(not_in_top5)/total*100:.2f}% of total)")

hc_errors = [r for r in top1_failures if r["top1_confidence"] >= 0.80]
hc_errors.sort(key=lambda x: x["top1_confidence"], reverse=True)
print(f"High-Confidence Errors (>=80%): {len(hc_errors)} ({len(hc_errors)/len(top1_failures)*100:.2f}% of failures)")

lc_correct = [r for r in data if r["is_top1_correct"] and r["top1_confidence"] < 0.30]
print(f"Low-Confidence Correct (<30%): {len(lc_correct)}")

print("\n--- WORST 10 SPECIES ---")
sp_sorted = sorted(species_accuracy_rows, key=lambda x: (x["accuracy_percent"], x["total_images"]))
for r in sp_sorted[:10]:
    print(f"{r['actual_cub_class_name']:<35} | Acc: {r['accuracy_percent']:5.1f}% | ({r['correct_count']}/{r['total_images']}) | AvgConf: {r['average_confidence']*100:.1f}%")

print("\n--- BEST 10 SPECIES ---")
sp_best = sorted(species_accuracy_rows, key=lambda x: (x["accuracy_percent"], x["total_images"]), reverse=True)
for r in sp_best[:10]:
    print(f"{r['actual_cub_class_name']:<35} | Acc: {r['accuracy_percent']:5.1f}% | ({r['correct_count']}/{r['total_images']}) | AvgConf: {r['average_confidence']*100:.1f}%")

print("\n--- TOP 10 CONFUSION PAIRS ---")
for r in confusion_rows[:10]:
    print(f"Actual: {r['actual_cub_class_name']:<30} -> Pred: {r['predicted_species']:<25} | Count: {r['count']} | AvgConf: {r['average_confidence']*100:.1f}%")

print("\n--- CONFIDENCE CALIBRATION ---")
for r in calibration_rows:
    print(f"Bin: {r['bin_range']:<8} | Total: {r['total_predictions']:<5} | Correct: {r['correct_count']:<5} | Acc: {r['accuracy_percent']:5.1f}% | AvgConf: {r['average_confidence']*100:.1f}%")

print("\n--- LATENCY BREAKDOWN ---")
print(json.dumps(latency_summary, indent=2))
