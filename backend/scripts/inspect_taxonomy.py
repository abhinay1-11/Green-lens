import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from bioclip.predict import TreeOfLifeClassifier

clf = TreeOfLifeClassifier()
df = clf.get_label_data()
print("Label Data Columns:", df.columns.tolist())
print("Label Data Shape:", df.shape)
print("\nSample Rows:")
print(df.head(5)[["kingdom", "phylum", "class", "order", "family", "genus", "species", "common_name"]])
