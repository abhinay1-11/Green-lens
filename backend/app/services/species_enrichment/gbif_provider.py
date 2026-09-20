from typing import Dict, Any, List, Optional
from app.services.species_enrichment.models import SpeciesTaxonomy, ReferenceImage
from app.services.species_enrichment.session import get_http_session

GBIF_MATCH_URL = "https://api.gbif.org/v1/species/match"
GBIF_SPECIES_URL = "https://api.gbif.org/v1/species"
TIMEOUT = 4.0

def fetch_gbif_species_data(scientific_name: str) -> Dict[str, Any]:
    """
    Fetches taxonomy, media (images), and descriptions from GBIF for a given scientific name.
    """
    result = {
        "taxonomy": None,
        "reference_images": [],
        "description": None,
        "source": "GBIF (Global Biodiversity Information Facility)"
    }

    if not scientific_name:
        return result

    try:
        # 1. Match species name
        session = get_http_session()
        match_resp = session.get(GBIF_MATCH_URL, params={"name": scientific_name, "strict": "false"}, timeout=TIMEOUT)
        if match_resp.status_code != 200:
            return result
        
        match_data = match_resp.json()
        if match_data.get("matchType") == "NONE" or not match_data.get("usageKey"):
            return result

        usage_key = match_data["usageKey"]

        # Parse taxonomy
        taxonomy = SpeciesTaxonomy(
            kingdom=match_data.get("kingdom"),
            phylum=match_data.get("phylum"),
            class_name=match_data.get("class"),
            order=match_data.get("order"),
            family=match_data.get("family"),
            genus=match_data.get("genus"),
            species=match_data.get("species") or match_data.get("canonicalName"),
            rank=match_data.get("rank") or "Species"
        )
        result["taxonomy"] = taxonomy

        # 2. Fetch Media
        try:
            media_resp = session.get(f"{GBIF_SPECIES_URL}/{usage_key}/media", timeout=TIMEOUT)
            if media_resp.status_code == 200:
                media_data = media_resp.json()
                results = media_data.get("results", [])
                
                images: List[ReferenceImage] = []
                seen_urls = set()

                for item in results:
                    # Filter to image types only
                    item_type = str(item.get("type", "")).lower()
                    mime_type = str(item.get("format", "")).lower()
                    
                    is_img = "stillimage" in item_type or "image" in item_type or "image" in mime_type or "jpeg" in mime_type or "png" in mime_type or "jpg" in mime_type
                    if not is_img:
                        continue

                    img_url = item.get("identifier")
                    if not img_url or not isinstance(img_url, str) or not img_url.startswith("http"):
                        continue

                    if img_url in seen_urls:
                        continue
                    seen_urls.add(img_url)

                    creator = item.get("creator") or item.get("rightsHolder") or item.get("publisher") or "Unknown Creator"
                    license_str = item.get("license") or "CC BY"
                    source_url = item.get("references") or item.get("source") or img_url

                    # Normalize license text if it is a URL
                    license_name = license_str
                    license_url = None
                    if license_str.startswith("http"):
                        license_url = license_str
                        if "by/4.0" in license_str:
                            license_name = "CC BY 4.0"
                        elif "by-nc" in license_str:
                            license_name = "CC BY-NC 4.0"
                        elif "publicdomain" in license_str or "zero" in license_str:
                            license_name = "CC0 Public Domain"
                        else:
                            license_name = "Creative Commons"

                    images.append(ReferenceImage(
                        url=img_url,
                        thumbnail_url=img_url,
                        source="GBIF",
                        creator=str(creator),
                        license=license_name,
                        license_url=license_url
                    ))

                    if len(images) >= 6:
                        break

                result["reference_images"] = images
        except Exception as media_err:
            print(f"[GBIFProvider] Media fetch error for '{scientific_name}': {media_err}")

        # 3. Fetch Description
        try:
            desc_resp = session.get(f"{GBIF_SPECIES_URL}/{usage_key}/descriptions", timeout=TIMEOUT)
            if desc_resp.status_code == 200:
                desc_data = desc_resp.json()
                for d in desc_data.get("results", []):
                    desc_text = d.get("description")
                    if desc_text and len(desc_text.strip()) > 30:
                        result["description"] = desc_text.strip()
                        break
        except Exception as desc_err:
            print(f"[GBIFProvider] Description fetch error for '{scientific_name}': {desc_err}")

    except Exception as exc:
        print(f"[GBIFProvider] Exception looking up '{scientific_name}': {exc}")

    return result
