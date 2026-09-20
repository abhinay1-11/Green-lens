import csv
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
csv_path = os.path.join(project_root, "data", "datasets", "CUB_200_2011", "bioclip_results.csv")

with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i < 10:
            print(f"Row {i+1}:")
            print(f"  Actual CUB Class: {row['actual_cub_class_name']}")
            print(f"  Top1 Sci:         {row['bioclip_top1_species']}")
            print(f"  Top1 Common:      {row['bioclip_top1_common_name']}")
            print(f"  Top3 String:      {row['top3_predictions']}")
            print(f"  is_top1_correct:  {row['is_top1_correct']}")
