import os
import sys
import requests

# Ensure UTF-8 output encoding for Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/test_images"))
img_path = os.path.join(DATA_DIR, "birds/sparrow_distant.jpg")

print("--- Testing iNaturalist Vision Endpoint directly with different Headers ---")

with open(img_path, "rb") as f:
    img_bytes = f.read()

url = "https://api.inaturalist.org/v1/computervision/score_observation"

# Test 1: Default python-requests header
print("\nTest 1: Default requests headers")
try:
    files = {"image": ("bird.jpg", img_bytes, "image/jpeg")}
    data = {"taxon_id": 3}
    r = requests.post(url, files=files, data=data, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Response snippet: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Custom User-Agent header
print("\nTest 2: Custom User-Agent header")
try:
    headers = {
        "User-Agent": "GreenLensBiodiversityApp/1.0 (contact@greenlens.org)",
        "Accept": "application/json"
    }
    files = {"image": ("bird.jpg", img_bytes, "image/jpeg")}
    data = {"taxon_id": 3}
    r = requests.post(url, files=files, data=data, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Response snippet: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")
