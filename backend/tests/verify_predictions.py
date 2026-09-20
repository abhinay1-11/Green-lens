"""
Verification script for testing GreenLens AI Species Identification Providers & Prediction API (Phases 2 & 3).
"""
import os
import sys
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.services.identification.factory import get_identification_provider
from app.services.identification.mock import MockProvider
from app.services.identification.plantnet import PlantNetProvider
from app.utils.confidence import format_confidence_percentage

def create_sample_image_bytes(color="green") -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (300, 300), color=color)
    img.save(buf, format="JPEG")
    return buf.getvalue()

def verify_all():
    print("=== GreenLens AI Model Provider Verification (Phases 2 & 3) ===")

    # 1. Test Mock Provider (Dev Mode)
    print("\n1. Testing MockProvider (Explicit Mock Mode):")
    plant_mock = MockProvider()
    res_plant = plant_mock.identify([], category="plant")
    print(f"   Success: {res_plant.success}")
    print(f"   Provider: {res_plant.provider}")
    print(f"   Status: {res_plant.identification_status}")
    print(f"   Top Prediction: {res_plant.predictions[0].scientific_name} ({res_plant.predictions[0].common_names[0]})")
    assert res_plant.success is True
    assert res_plant.is_mock is True

    # 2. Test PlantNetProvider Unconfigured Mode (No Fake Results)
    print("\n2. Testing PlantNetProvider in Real Mode (Unconfigured Key Test):")
    plantnet_prov = PlantNetProvider(api_key="")
    res_unconfig = plantnet_prov.identify([{"file_bytes": create_sample_image_bytes()}], category="plant")
    print(f"   Success: {res_unconfig.success}")
    print(f"   Provider: {res_unconfig.provider}")
    print(f"   Identification Status: {res_unconfig.identification_status}")
    print(f"   Error Code: {res_unconfig.error.code if res_unconfig.error else 'None'}")
    print(f"   Error Message: {res_unconfig.error.message if res_unconfig.error else 'None'}")
    assert res_unconfig.success is False
    assert res_unconfig.error.code == "PLANT_PROVIDER_NOT_CONFIGURED"
    assert len(res_unconfig.predictions) == 0, "Real mode must NOT invent fake predictions when provider is unconfigured!"

    # 3. Test REST Endpoint POST /api/identification/predict in Mock Mode
    print("\n3. Testing REST Endpoint POST /api/identification/predict (Mock Mode):")
    settings.IDENTIFICATION_MODE = "mock"
    client = TestClient(app)

    img_bytes = create_sample_image_bytes()
    files = [("images", ("leaf_sample.jpg", img_bytes, "image/jpeg"))]
    data = {"category": "plant", "organs": ["leaf"]}

    response = client.post("/api/identification/predict", files=files, data=data)
    print(f"   HTTP Response Code: {response.status_code}")
    assert response.status_code == 200

    json_body = response.json()
    print("   Response Payload Structure:")
    print(f"     * success: {json_body.get('success')}")
    print(f"     * provider: {json_body.get('provider')}")
    print(f"     * identification_status: {json_body.get('identification_status')}")
    print(f"     * predictions count: {len(json_body.get('predictions', []))}")
    for pred in json_body.get("predictions", [])[:3]:
        pct = format_confidence_percentage(pred['confidence'])
        print(f"       Rank #{pred['rank']}: {pred['scientific_name']} ({pred.get('common_names', [''])[0]}) -> {pct}")

    # Reset mode back to real
    settings.IDENTIFICATION_MODE = "real"
    print("\n[SUCCESS] Phase 2 & Phase 3 Provider Architecture & Plant Verification Completed!")

if __name__ == "__main__":
    verify_all()
