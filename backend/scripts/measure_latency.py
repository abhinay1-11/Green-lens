import time
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.species_enrichment import SpeciesEnrichmentService
from app.services.identification.factory import get_identification_provider

def measure_benchmark():
    print("=== LATENCY BENCHMARK ===")
    
    # 1. Species Search Benchmark (First vs Second)
    t0 = time.perf_counter()
    p1 = SpeciesEnrichmentService.get_species_profile("Corvus brachyrhynchos", "American Crow", "bird")
    t1 = time.perf_counter()
    print(f"First Species Enrichment Request: {(t1 - t0)*1000:.2f} ms")

    t2 = time.perf_counter()
    p2 = SpeciesEnrichmentService.get_species_profile("Corvus brachyrhynchos", "American Crow", "bird")
    t3 = time.perf_counter()
    print(f"Second Species Enrichment Request (Cached): {(t3 - t2)*1000:.2f} ms")

    # 2. Bird Identification Provider Benchmark
    t4 = time.perf_counter()
    provider = get_identification_provider("bird")
    t5 = time.perf_counter()
    print(f"First BioCLIP Provider Load / Init: {(t5 - t4)*1000:.2f} ms")

    t6 = time.perf_counter()
    provider_again = get_identification_provider("bird")
    t7 = time.perf_counter()
    print(f"Second BioCLIP Provider Retrieve: {(t7 - t6)*1000:.2f} ms")

if __name__ == "__main__":
    measure_benchmark()
