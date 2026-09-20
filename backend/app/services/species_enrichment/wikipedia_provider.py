import re
from typing import Dict, Any, Optional
from app.services.species_enrichment.models import SpeciesFacts, ReferenceImage
from app.services.species_enrichment.session import get_http_session

WIKIPEDIA_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
TIMEOUT = 4.0

def _clean_title(title: str) -> str:
    return title.strip().replace(" ", "_")

def fetch_wikipedia_species_data(scientific_name: str, common_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches Wikipedia lead summary, thumbnail/original image, and facts for a given species.
    """
    result = {
        "description": None,
        "facts": SpeciesFacts(),
        "reference_images": [],
        "source": "Wikipedia"
    }

    titles_to_try = []
    if scientific_name:
        titles_to_try.append(_clean_title(scientific_name))
    if common_name and common_name.lower() != scientific_name.lower():
        titles_to_try.append(_clean_title(common_name))

    session = get_http_session()

    for title in titles_to_try:
        try:
            url = f"{WIKIPEDIA_SUMMARY_URL}{title}"
            resp = session.get(url, timeout=TIMEOUT)
            
            if resp.status_code == 200:
                data = resp.json()
                page_type = data.get("type", "")
                
                if page_type in ["standard", "disambiguation"]:
                    extract = data.get("extract")
                    if extract:
                        result["description"] = extract.strip()
                        
                        # Extract structured facts from text if present
                        facts = _extract_facts_from_text(extract)
                        result["facts"] = facts

                    # Extract image
                    orig_img = data.get("originalimage", {}).get("source")
                    thumb_img = data.get("thumbnail", {}).get("source")
                    
                    if orig_img or thumb_img:
                        img_url = orig_img or thumb_img
                        result["reference_images"].append(ReferenceImage(
                            url=img_url,
                            thumbnail_url=thumb_img or img_url,
                            source="Wikimedia Commons / Wikipedia",
                            creator="Wikipedia Contributors",
                            license="CC BY-SA 4.0",
                            license_url="https://creativecommons.org/licenses/by-sa/4.0/"
                        ))
                    
                    if result["description"]:
                        break  # Found good match
        except Exception as exc:
            print(f"[WikipediaProvider] Error querying '{title}': {exc}")

    return result

def _extract_facts_from_text(text: str) -> SpeciesFacts:
    """
    Parses facts (habitat, diet, behavior, reproduction, conservation) from summary text using pattern matching.
    Ensures unmentioned facts default to "Information unavailable".
    """
    facts = SpeciesFacts(
        habitat=None,
        diet=None,
        behavior=None,
        reproduction=None,
        conservation=None
    )

    sentences = re.split(r'\. |\n', text)

    for s in sentences:
        s_lower = s.lower()
        if facts.habitat is None and any(w in s_lower for w in ["habitat", "found in", "native to", "inhabits", "endemic to", "ranges from", "forests", "grasslands", "shrubland", "sagebrush"]):
            facts.habitat = s.strip() + "."
        elif facts.diet is None and any(w in s_lower for w in ["feeds on", "diet", "eats", "herbivore", "carnivore", "omnivore", "preys on", "seeds", "insects", "leaves", "forages"]):
            facts.diet = s.strip() + "."
        elif facts.behavior is None and any(w in s_lower for w in ["behavior", "migratory", "nocturnal", "diurnal", "display", "mating", "social", "territorial"]):
            facts.behavior = s.strip() + "."
        elif facts.reproduction is None and any(w in s_lower for w in ["breeds", "nest", "clutch", "eggs", "reproduction", "offspring", "gestation", "mating"]):
            facts.reproduction = s.strip() + "."
        elif facts.conservation is None and any(w in s_lower for w in ["threatened", "endangered", "vulnerable", "least concern", "conservation", "extinction", "iucn", "protected"]):
            facts.conservation = s.strip() + "."

    # Ensure any unpopulated fact defaults to "Information unavailable"
    if facts.habitat is None: facts.habitat = "Information unavailable"
    if facts.diet is None: facts.diet = "Information unavailable"
    if facts.behavior is None: facts.behavior = "Information unavailable"
    if facts.reproduction is None: facts.reproduction = "Information unavailable"
    if facts.conservation is None: facts.conservation = "Information unavailable"

    return facts
