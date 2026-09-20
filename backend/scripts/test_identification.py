"""
Automated Model Identification Evaluation Script for GreenLens.
Evaluates model predictions across Plants, Birds, Insects, and Unknown test image datasets.
"""
import os
import sys
import time
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.services.identification.factory import get_identification_provider
from app.utils.confidence import format_confidence_percentage

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "test_images"))

def evaluate_category(category_name: str, folder_name: str):
    print(f"\n=========================================")
    print(f"EVALUATING CATEGORY: {category_name.upper()}")
    print(f"=========================================")

    folder_path = os.path.join(DATA_DIR, folder_name)
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    if not files:
        print(f"No test images found in {folder_path}")
        return

    provider = get_identification_provider(category_name)

    for filename in files:
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        images = [{"file_bytes": file_bytes, "filename": filename, "organ": "auto"}]
        
        start_time = time.time()
        result = provider.identify(images, category=category_name)
        elapsed = round(time.time() - start_time, 3)

        print(f"\nIMAGE: {filename}")
        print(f"CATEGORY: {result.category}")
        print(f"PROVIDER: {result.provider}")
        print(f"MODEL: {result.model_name or 'N/A'}")
        print(f"STATUS: {result.identification_status}")
        print(f"PROCESSING TIME: {elapsed} sec")
        print(f"SUCCESS: {result.success}")

        if result.success and result.predictions:
            for pred in result.predictions[:3]:
                pct = format_confidence_percentage(pred.confidence)
                c_name = pred.common_names[0] if pred.common_names else ""
                print(f"  #{pred.rank} {pred.scientific_name} ({c_name}) — {pct} [{pred.taxonomic_rank}]")
        elif result.error:
            print(f"  ERROR [{result.error.code}]: {result.error.message}")

def run_evaluation():
    print("=== GreenLens AI Species Identification Pipeline Benchmark ===")
    print(f"Mode: {settings.IDENTIFICATION_MODE}")

    evaluate_category("plant", "plants")
    evaluate_category("bird", "birds")
    evaluate_category("insect", "insects")
    evaluate_category("unknown", "unknown")

    print("\n=========================================")
    print("BENCHMARK & EVALUATION COMPLETE")
    print("=========================================\n")

if __name__ == "__main__":
    run_evaluation()
