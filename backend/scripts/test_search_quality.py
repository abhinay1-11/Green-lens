import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.routers.species import search_species

def test_queries():
    db = SessionLocal()
    try:
        queries = ["crow", "sparrow", "neem", "Apis mellifera"]
        for q in queries:
            print(f"\n--- QUERY: '{q}' ---")
            results = search_species(q=q, category=None, db=db)
            for i, sp in enumerate(results[:5], 1):
                print(f" {i}. {sp.common_name} ({sp.scientific_name}) -> Category: {sp.category}")
                print(f"    Facts Habitat: {sp.habitat[:50]}...")
    finally:
        db.close()

if __name__ == "__main__":
    test_queries()
