import os
import sys
import time

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.identification.bioclip import BioCLIPBirdProvider

bird_dir = os.path.join(os.path.dirname(backend_dir), "data", "test_images", "birds")
image_files = [
    "Female_Greater_Sage-Grouse.webp",
    "parrot_closeup.jpg",
    "peacock_sample.jpg",
    "sparrow_distant.jpg"
]

provider = BioCLIPBirdProvider()

print("=" * 70)
print("GREENLENS — BIOCLIP 2 BIRD IDENTIFICATION INTEGRATION SUITE TEST")
print("=" * 70)

for filename in image_files:
    filepath = os.path.join(bird_dir, filename)
    if not os.path.exists(filepath):
        print(f"[-] {filename}: FILE NOT FOUND ({filepath})")
        continue

    with open(filepath, "rb") as f:
        file_bytes = f.read()

    t0 = time.time()
    response = provider.identify(
        [{"file_bytes": file_bytes, "filename": filename}],
        category="bird"
    )
    elapsed_ms = (time.time() - t0) * 1000

    if response.success and response.predictions:
        top = response.predictions[0]
        c_name = top.common_names[0] if top.common_names else "N/A"
        print(f"[+] Image: {filename}")
        print(f"    Top Prediction: {c_name} ({top.scientific_name})")
        print(f"    Confidence:     {top.confidence * 100:.1f}% ({top.confidence:.4f})")
        print(f"    Status:         {response.identification_status}")
        print(f"    Latency:        {elapsed_ms:.1f} ms")
        print(f"    Provider:       {response.provider}")
        print("-" * 70)
    else:
        err_msg = response.error.message if response.error else "Unknown error"
        print(f"[-] Image: {filename} FAILED: {err_msg}")
        print("-" * 70)
