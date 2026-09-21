import os
import sys
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

client = TestClient(app)

print("=" * 70)
print("TESTING FASTAPI /api/providers/status ENDPOINT")
print("=" * 70)
status_res = client.get("/api/providers/status")
print("HTTP Status Code:", status_res.status_code)
print("Response JSON:", status_res.json())

assert status_res.status_code == 200
assert status_res.json()["bird"]["provider"] in ("BioCLIP 2", "legacy_bird_ai", "legacy_pytorch")

print("\n" + "=" * 70)
print("TESTING FASTAPI /api/identification/predict (BIRD CATEGORY)")
print("=" * 70)

test_img_path = os.path.join(os.path.dirname(backend_dir), "data", "test_images", "birds", "Female_Greater_Sage-Grouse.webp")

with open(test_img_path, "rb") as f:
    files = [("images", ("Female_Greater_Sage-Grouse.webp", f.read(), "image/webp"))]
    data = {"category": "bird"}
    res = client.post("/api/identification/predict", files=files, data=data)

print("HTTP Status Code:", res.status_code)
print("Response JSON:")
import json
print(json.dumps(res.json(), indent=2))

body = res.json()
assert res.status_code == 200
assert body["success"] is True
assert body["category"] == "bird"
assert body["provider"] in ("BioCLIP 2", "legacy_bird_ai", "bird_local_ai")

print("\n" + "=" * 70)
print("ALL LIVE API ENDPOINT VERIFICATIONS PASSED SUCCESSFULLY!")
print("=" * 70)
