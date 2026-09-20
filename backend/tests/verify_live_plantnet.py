"""
Verification script for testing LIVE Pl@ntNet API Key with real plant identification requests.
"""
import os
import sys
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image
from app.config import settings
from app.services.identification.plantnet import PlantNetProvider
from app.utils.confidence import format_confidence_percentage

def create_sample_leaf_image() -> bytes:
    buf = io.BytesIO()
    # Create green leaf-like shape image
    img = Image.new("RGB", (500, 500), color=(34, 139, 34))
    img.save(buf, format="JPEG")
    return buf.getvalue()

def verify_live_plantnet():
    print("=== Testing Live Pl@ntNet API Key Integration ===")
    
    clean_key = settings.clean_plantnet_api_key
    print(f"Key Present: {bool(clean_key)}")
    print(f"Key Length: {len(clean_key)}")
    print(f"Mode: {settings.IDENTIFICATION_MODE}")

    provider = PlantNetProvider()
    image_bytes = create_sample_leaf_image()
    images = [{"file_bytes": image_bytes, "filename": "test_leaf.jpg", "organ": "leaf"}]

    print("\nSending identification request to Pl@ntNet API v2...")
    result = provider.identify(images, category="plant")

    print("\n--- Live Pl@ntNet Response ---")
    print(f"Success: {result.success}")
    print(f"Provider: {result.provider}")
    print(f"Model Version: {result.model_version}")
    print(f"Identification Status: {result.identification_status}")

    if result.success and result.predictions:
        print(f"\nTop Species Predictions ({len(result.predictions)} candidates returned):")
        for pred in result.predictions:
            pct = format_confidence_percentage(pred.confidence)
            c_name = pred.common_names[0] if pred.common_names else "No common name"
            print(f"  Rank #{pred.rank}: {pred.scientific_name} ({c_name}) — {pct}")
        print("\n[SUCCESS] Live Pl@ntNet API key verified and returning real model species predictions!")
    elif result.error:
        print(f"\n[ERROR] Code: {result.error.code}")
        print(f"Message: {result.error.message}")

if __name__ == "__main__":
    verify_live_plantnet()
