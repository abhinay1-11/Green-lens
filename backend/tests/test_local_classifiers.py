import os
import sys
import time
from PIL import Image

# Ensure UTF-8 console encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/test_images"))

print("==========================================================")
print("TESTING LOCAL PRETRAINED SPECIES MODELS VIA TRANSFORMERS/TIMM")
print("==========================================================")

from transformers import pipeline

# 1. Test Bird Local Model
bird_path = os.path.join(DATA_DIR, "birds/sparrow_distant.jpg")
print(f"\n--- Testing Bird Local Model on '{os.path.basename(bird_path)}' ---")

start_t = time.time()
try:
    # Pretrained bird species classification pipeline
    bird_classifier = pipeline("image-classification", model="dima806/bird_species_detection", device="cpu")
    load_t = time.time() - start_t
    print(f"Bird model loaded successfully in {load_t:.2f}s")

    img = Image.open(bird_path).convert("RGB")
    infer_start = time.time()
    results = bird_classifier(img, top_k=5)
    infer_t = time.time() - infer_start

    print(f"Bird Inference complete in {infer_t*1000:.1f}ms:")
    for idx, item in enumerate(results, start=1):
        print(f"  Rank {idx}: {item['label']} | Score: {item['score']*100:.1f}%")

except Exception as err:
    print(f"Bird model test error: {err}")

# 2. Test Insect Local Model
insect_path = os.path.join(DATA_DIR, "insects/butterfly_monarch.jpg")
print(f"\n--- Testing Insect Local Model on '{os.path.basename(insect_path)}' ---")

start_t = time.time()
try:
    insect_classifier = pipeline("image-classification", model="dima806/insect_species_detection", device="cpu")
    load_t = time.time() - start_t
    print(f"Insect model loaded successfully in {load_t:.2f}s")

    img = Image.open(insect_path).convert("RGB")
    infer_start = time.time()
    results = insect_classifier(img, top_k=5)
    infer_t = time.time() - infer_start

    print(f"Insect Inference complete in {infer_t*1000:.1f}ms:")
    for idx, item in enumerate(results, start=1):
        print(f"  Rank {idx}: {item['label']} | Score: {item['score']*100:.1f}%")

except Exception as err:
    print(f"Insect model test error: {err}")

print("\n==========================================================")
print("LOCAL MODEL EVALUATION COMPLETE")
print("==========================================================")
