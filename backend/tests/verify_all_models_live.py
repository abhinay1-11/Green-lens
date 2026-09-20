import os
import sys
import json

# Ensure UTF-8 output encoding for Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.services.identification.plantnet import PlantNetProvider
from app.services.identification.bird import BirdProvider
from app.services.identification.insect import InsectProvider
from app.services.identification.biodiversity_fallback import BiodiversityFallbackProvider
from app.services.identification.unknown_router import UnknownCategoryRouter
from app.services.identification.factory import get_identification_provider

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/test_images"))

def verify_all_models():
    print("==========================================================")
    print("LIVE SPECIES IDENTIFICATION MODEL VERIFICATION")
    print(f"IDENTIFICATION_MODE: {settings.IDENTIFICATION_MODE}")
    print("==========================================================\n")

    test_cases = [
        ("PLANT / TREE ENGINE (Pl@ntNet + Fallback)", "plant", "trees/mango_tree_full.jpg", PlantNetProvider()),
        ("BIRD ENGINE (Aves Vision + Fallback)", "bird", "birds/sparrow_distant.jpg", BirdProvider()),
        ("INSECT ENGINE (Insecta Vision + Fallback)", "insect", "insects/butterfly_monarch.jpg", InsectProvider()),
        ("GENERAL BIODIVERSITY ENGINE (iNaturalist Vision)", "general", "plants/flower_sample.jpg", BiodiversityFallbackProvider()),
        ("UNKNOWN CATEGORY ROUTER (Auto Category Detection)", "unknown", "insects/bee_sample.jpg", UnknownCategoryRouter())
    ]

    for label, category, subpath, provider in test_cases:
        img_path = os.path.join(DATA_DIR, subpath)
        print(f"----------------------------------------------------------")
        print(f"TESTING: {label}")
        print(f"Category: '{category}' | Image: {subpath}")
        print(f"----------------------------------------------------------")

        if not os.path.exists(img_path):
            print(f"[ERROR] Sample image not found at {img_path}\n")
            continue

        with open(img_path, "rb") as f:
            file_bytes = f.read()

        images = [{
            "file_bytes": file_bytes,
            "filename": os.path.basename(subpath),
            "organ": "auto"
        }]

        try:
            response = provider.identify(images, category=category)
            
            print(f"Success:                {response.success}")
            print(f"Provider Name:          {response.provider}")
            print(f"Model Name:             {response.model_name}")
            print(f"Model Version:          {response.model_version}")
            print(f"Identification Status:  {response.identification_status}")

            if response.error:
                print(f"Error Code:             {response.error.code}")
                print(f"Error Message:          {response.error.message}")

            if response.predictions:
                print(f"\nTop Predictions (Count: {len(response.predictions)}):")
                for pred in response.predictions[:3]:
                    c_name = pred.common_names[0] if pred.common_names else 'N/A'
                    print(f"  Rank {pred.rank}: {pred.scientific_name} ({c_name}) | Confidence: {pred.confidence * 100:.1f}%")
            else:
                print("No predictions returned.")

        except Exception as exc:
            print(f"[EXCEPTION]: {exc}")

        print("\n")

    print("==========================================================")
    print("VERIFICATION COMPLETE")
    print("==========================================================")

if __name__ == "__main__":
    verify_all_models()
