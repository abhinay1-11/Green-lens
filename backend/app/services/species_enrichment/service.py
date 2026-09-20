import traceback
from typing import Optional, Dict, Any, List

from app.services.species_enrichment.models import (
    SpeciesProfile, SpeciesTaxonomy, SpeciesFacts, ReferenceImage
)
from app.services.species_enrichment.cache import (
    get_cached_species_profile, set_cached_species_profile
)
from app.services.species_enrichment.gbif_provider import fetch_gbif_species_data
from app.services.species_enrichment.wikipedia_provider import fetch_wikipedia_species_data

class SpeciesEnrichmentService:
    @staticmethod
    def get_species_profile(
        scientific_name: str,
        common_name: Optional[str] = None,
        category: Optional[str] = None
    ) -> SpeciesProfile:
        if not scientific_name or not isinstance(scientific_name, str):
            return SpeciesProfile(
                available=False,
                scientific_name=scientific_name or "Unknown",
                common_name=common_name
            )

        scientific_name_clean = scientific_name.strip()

        # 1. Check SQLite Cache
        try:
            cached_data = get_cached_species_profile(scientific_name_clean)
            if cached_data:
                print(f"[SpeciesEnrichment] Cache hit for '{scientific_name_clean}'")
                return SpeciesProfile(**cached_data)
        except Exception as cache_err:
            print(f"[SpeciesEnrichment] Cache read error: {cache_err}")

        print(f"[SpeciesEnrichment] Cache miss for '{scientific_name_clean}'. Fetching from external APIs...")

        # 2. Fetch from GBIF and Wikipedia concurrently
        gbif_data = {}
        wiki_data = {}

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_gbif = executor.submit(fetch_gbif_species_data, scientific_name_clean)
            future_wiki = executor.submit(fetch_wikipedia_species_data, scientific_name_clean, common_name)

            try:
                gbif_data = future_gbif.result(timeout=4.0) or {}
            except Exception as g_err:
                print(f"[SpeciesEnrichment] GBIF error for '{scientific_name_clean}': {g_err}")

            try:
                wiki_data = future_wiki.result(timeout=4.0) or {}
            except Exception as w_err:
                print(f"[SpeciesEnrichment] Wikipedia error for '{scientific_name_clean}': {w_err}")

        # 3. Combine Provider Results
        taxonomy = gbif_data.get("taxonomy") or SpeciesTaxonomy(species=scientific_name_clean)

        # Merge Description: prefer Wikipedia, fallback to GBIF
        description = wiki_data.get("description") or gbif_data.get("description")

        # Merge Facts: Wikipedia facts
        facts = wiki_data.get("facts") or SpeciesFacts()

        # Merge Reference Images: Combine Wikipedia + GBIF, deduplicate
        combined_images: List[ReferenceImage] = []
        seen_urls = set()

        for img in wiki_data.get("reference_images", []):
            if img.url not in seen_urls:
                seen_urls.add(img.url)
                combined_images.append(img)

        for img in gbif_data.get("reference_images", []):
            if img.url not in seen_urls:
                seen_urls.add(img.url)
                combined_images.append(img)
            if len(combined_images) >= 6:
                break

        # Sources list
        sources = []
        if category == "bird":
            sources.append("Cornell BirdNET Taxonomy")
        if wiki_data.get("description"):
            sources.append("Wikipedia API")
        if gbif_data.get("taxonomy"):
            sources.append("GBIF Species API")

        if not sources:
            sources.append("GBIF / Open Biodiversity API")

        # Determine availability
        has_any_data = bool(description or (combined_images and len(combined_images) > 0) or gbif_data.get("taxonomy"))

        profile = SpeciesProfile(
            available=has_any_data,
            scientific_name=scientific_name_clean,
            common_name=common_name,
            description=description,
            taxonomy=taxonomy,
            facts=facts,
            reference_images=combined_images,
            sources=sources
        )

        # 4. Save to Cache
        try:
            profile_dict = profile.model_dump(mode="json")
            set_cached_species_profile(scientific_name_clean, profile_dict)
        except Exception as save_err:
            print(f"[SpeciesEnrichment] Error writing to cache: {save_err}")

        return profile
