import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("Checking bioclip python module...")

try:
    import bioclip
    print("bioclip package version/module:", bioclip)
    from bioclip import TreeOfLifeClassifier
    print("TreeOfLifeClassifier imported successfully!")
except Exception as e:
    print("bioclip import error:", e)
