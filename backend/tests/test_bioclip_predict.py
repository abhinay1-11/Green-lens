import os
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from bioclip import TreeOfLifeClassifier, Rank

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/test_images"))
test_img = os.path.join(DATA_DIR, "birds/Female_Greater_Sage-Grouse.webp")

print("Initializing BioCLIP TreeOfLifeClassifier...")
start_t = time.time()
clf = TreeOfLifeClassifier()
init_t = time.time() - start_t
print(f"Classifier initialized in {init_t:.2f}s")

print(f"\nPredicting species for '{os.path.basename(test_img)}'...")
pred_start = time.time()
results = clf.predict(test_img, rank=Rank.SPECIES, k=5)
pred_t = time.time() - pred_start

print(f"\nPrediction complete in {pred_t*1000:.1f}ms:")
print("Type of results:", type(results))
for idx, res in enumerate(results, start=1):
    print(f"\nRank {idx}:")
    if isinstance(res, dict):
        for k, v in res.items():
            print(f"  {k}: {v}")
    else:
        print(f"  {res}")
