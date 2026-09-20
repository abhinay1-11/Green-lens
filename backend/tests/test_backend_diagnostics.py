import os
import sys
import io
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

def create_sample_jpeg():
    buf = io.BytesIO()
    img = Image.new("RGB", (400, 400), color="green")
    img.save(buf, format="JPEG")
    return buf.getvalue()

def run_backend_verification():
    client = TestClient(app)
    print("=== Section 10 Backend API Endpoint Verification ===")

    # 1. GET /api/health
    res_health = client.get("/api/health")
    print(f"\n1. GET /api/health: {res_health.status_code}")
    print(f"   Payload: {res_health.json()}")
    assert res_health.status_code == 200

    # 2. GET /api/providers/status
    res_status = client.get("/api/providers/status")
    print(f"\n2. GET /api/providers/status: {res_status.status_code}")
    print(f"   Payload: {res_status.json()}")
    assert res_status.status_code == 200
    assert "plant" in res_status.json()

    # 3. POST /api/identification/predict (Plant unconfigured test)
    settings.IDENTIFICATION_MODE = "real"
    settings.PLANTNET_API_KEY = ""
    
    img_bytes = create_sample_jpeg()
    files = [("images", ("leaf.jpg", img_bytes, "image/jpeg"))]
    data = {"category": "plant"}

    res_pred = client.post("/api/identification/predict", files=files, data=data)
    print(f"\n3. POST /api/identification/predict (Plant Unconfigured Key Test): {res_pred.status_code}")
    body = res_pred.json()
    print(f"   Success: {body.get('success')}")
    print(f"   Status: {body.get('identification_status')}")
    print(f"   Error: {body.get('error')}")
    assert body.get("success") is False
    assert body.get("error", {}).get("code") == "PLANT_PROVIDER_NOT_CONFIGURED"
    assert len(body.get("predictions", [])) == 0, "Must NOT return fake species when API key is unconfigured!"

    print("\n[SUCCESS] Section 10 Backend API Verification Completed Successfully!")

if __name__ == "__main__":
    run_backend_verification()
