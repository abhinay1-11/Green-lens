import csv
import json
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
analysis_dir = os.path.join(project_root, "data", "datasets", "CUB_200_2011", "analysis")

# 1. Top 30 Confusion Pairs
with open(os.path.join(analysis_dir, "genuine_error_pairs.csv"), "r", encoding="utf-8") as f:
    pairs = list(csv.DictReader(f))

print("=== TOP 15 GENUINE CONFUSION PAIRS ===")
for p in pairs[:15]:
    cnt = int(p['count'])
    print(f"Actual: {p['actual_cub_class_name']:<30} -> Pred: {p['predicted_species']:<25} | Count: {cnt:2d} | AvgConf: {float(p['average_confidence'])*100:5.1f}% | PctErr: {p['percentage_of_actual_species_errors']}%")

# 2. Species Error Rates
with open(os.path.join(analysis_dir, "genuine_species_error_rates.csv"), "r", encoding="utf-8") as f:
    sp_rates = list(csv.DictReader(f))

for s in sp_rates:
    s["genuine_error_rate_percent"] = float(s["genuine_error_rate_percent"])
    s["total_test_images"] = int(s["total_test_images"])
    s["canonical_accuracy_percent"] = float(s["canonical_accuracy_percent"])

print("\n=== TOP 20 HIGHEST GENUINE ERROR RATE SPECIES ===")
highest = sorted(sp_rates, key=lambda x: (x["genuine_error_rate_percent"], x["total_test_images"]), reverse=True)
for s in highest[:20]:
    print(f"  {s['actual_cub_class_name']:<35} | ErrorRate: {s['genuine_error_rate_percent']:5.1f}% | ({s['genuine_incorrect']}/{s['total_test_images']}) | Acc: {s['canonical_accuracy_percent']:5.1f}%")

print("\n=== TOP 20 LOWEST GENUINE ERROR RATE SPECIES ===")
lowest = sorted(sp_rates, key=lambda x: (x["genuine_error_rate_percent"], -x["total_test_images"]))
for s in lowest[:20]:
    print(f"  {s['actual_cub_class_name']:<35} | ErrorRate: {s['genuine_error_rate_percent']:5.1f}% | ({s['genuine_incorrect']}/{s['total_test_images']}) | Acc: {s['canonical_accuracy_percent']:5.1f}%")

# 3. Genuine Confidence Bins
with open(os.path.join(analysis_dir, "genuine_confidence_analysis.csv"), "r", encoding="utf-8") as f:
    conf_bins = list(csv.DictReader(f))

print("\n=== GENUINE ERROR CONFIDENCE BINS ===")
for b in conf_bins:
    print(f"  Bin: {b['bin_range']:<8} | Count: {b['genuine_error_count']:<4} | PctOfErrs: {float(b['percentage_of_genuine_errors']):5.2f}% | AvgConf: {float(b['average_confidence'])*100:5.1f}%")
