import requests
from typing import Dict, Any, Optional

GBIF_MATCH_URL = "https://api.gbif.org/v1/species/match"
GBIF_SPECIES_URL = "https://api.gbif.org/v1/species"

def lookup_gbif_taxonomy(scientific_name: str) -> Dict[str, Any]:
    """
    Queries GBIF Species Match REST API to retrieve canonical taxonomic breakdown.
    """
    if not scientific_name:
        return {}

    try:
        response = requests.get(GBIF_MATCH_URL, params={"name": scientific_name, "strict": "false"}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("matchType") != "NONE":
                return {
                    "usage_key": data.get("usageKey"),
                    "scientific_name": data.get("scientificName", scientific_name),
                    "canonical_name": data.get("canonicalName", scientific_name),
                    "kingdom": data.get("kingdom"),
                    "phylum": data.get("phylum"),
                    "class": data.get("class"),
                    "order": data.get("order"),
                    "family": data.get("family"),
                    "genus": data.get("genus"),
                    "species": data.get("species"),
                    "rank": data.get("rank")
                }
    except Exception as exc:
        print(f"GBIF taxonomy lookup error for {scientific_name}: {exc}")

    return {
        "scientific_name": scientific_name,
        "canonical_name": scientific_name
    }
