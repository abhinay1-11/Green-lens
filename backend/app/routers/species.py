import requests
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.species import Species
from app.models.observation import Observation
from app.schemas.species import SpeciesResponse
from app.services.species_enrichment import SpeciesEnrichmentService
from app.services.species_enrichment.session import get_http_session
from app.services.category_classifier import classify_category

router = APIRouter(prefix="/api/species", tags=["Species Explorer"])

GBIF_SEARCH_URL = "https://api.gbif.org/v1/species/search"
GBIF_MATCH_URL = "https://api.gbif.org/v1/species/match"
WIKIPEDIA_SEARCH_URL = "https://en.wikipedia.org/w/api.php"

HTTP_HEADERS = {"User-Agent": "GreenLens/1.0 (biodiversity-monitor; mailto:contact@greenlens.app)"}

# Curated default global species showcase list when search query is empty
DEFAULT_GLOBAL_SPECIES = [
    {"scientific_name": "Centrocercus urophasianus", "common_name": "Greater Sage-Grouse", "category": "bird"},
    {"scientific_name": "Azadirachta indica", "common_name": "Neem Tree", "category": "tree"},
    {"scientific_name": "Apis mellifera", "common_name": "Western Honey Bee", "category": "insect"},
    {"scientific_name": "Danaus plexippus", "common_name": "Monarch Butterfly", "category": "insect"},
    {"scientific_name": "Phoebastria nigripes", "common_name": "Black-footed Albatross", "category": "bird"},
    {"scientific_name": "Ficus religiosa", "common_name": "Sacred Fig", "category": "tree"},
    {"scientific_name": "Taraxacum officinale", "common_name": "Common Dandelion", "category": "plant"},
    {"scientific_name": "Turdus migratorius", "common_name": "American Robin", "category": "bird"},
    {"scientific_name": "Helianthus annuus", "common_name": "Common Sunflower", "category": "flower"},
]

def _category_matches(sp_cat: str, filter_cat: Optional[str]) -> bool:
    if not filter_cat or filter_cat.strip().lower() in ["all", "", "none"]:
        return True
    
    sp_cat_lower = (sp_cat or "").strip().lower()
    filter_lower = filter_cat.strip().lower()
    
    if filter_lower in ["birds", "bird"]:
        filter_lower = "bird"
    elif filter_lower in ["plants", "plant", "flowers", "flower"]:
        filter_lower = "plant"
    elif filter_lower in ["trees", "tree"]:
        filter_lower = "tree"
    elif filter_lower in ["insects", "insect"]:
        filter_lower = "insect"
    elif filter_lower in ["other", "others"]:
        filter_lower = "other"
        
    if filter_lower == "plant" and sp_cat_lower in ["plant", "tree", "flower"]:
        return True
    if filter_lower == "tree" and sp_cat_lower in ["tree", "plant"]:
        return True
    if filter_lower == "flower" and sp_cat_lower in ["flower", "plant"]:
        return True
        
    return sp_cat_lower == filter_lower


@router.get("/search", response_model=List[SpeciesResponse])
def search_species(
    q: Optional[str] = Query(None, description="Search term for scientific or common name"),
    category: Optional[str] = Query(None, description="Category filter (all, birds, plants, trees, insects, other)"),
    db: Session = Depends(get_db)
):
    """
    Global Species Search: Searches global species databases (GBIF & Wikipedia) 
    and incorporates local observation statistics if available.
    """
    results_map = {} # scientific_name.lower() -> dict
    api_error_occurred = False

    clean_q = q.strip() if q else ""

    # 1. Search Local Database first
    if clean_q:
        term = f"%{clean_q}%"
        local_species = db.query(Species).filter(
            (Species.scientific_name.ilike(term)) | (Species.common_name.ilike(term))
        ).limit(10).all()
        
        for sp in local_species:
            key = sp.scientific_name.strip().lower()
            results_map[key] = {
                "id": sp.id,
                "scientific_name": sp.scientific_name,
                "common_name": sp.common_name,
                "category": sp.category or "other"
            }

    # 2. Search GBIF Global Species Search API & Suggest API (handles common & scientific names)
    if clean_q and len(clean_q) >= 2:
        session = get_http_session()

        # 2A. GBIF Species Suggest API for high-confidence canonical species
        try:
            s_resp = session.get(
                "https://api.gbif.org/v1/species/suggest",
                params={"q": clean_q, "limit": 10},
                headers=HTTP_HEADERS,
                timeout=4.0
            )
            if s_resp.status_code == 200:
                s_data = s_resp.json()
                for item in s_data:
                    sci = item.get("canonicalName") or item.get("species") or item.get("scientificName")
                    rank = (item.get("rank") or "").upper()
                    kingdom = (item.get("kingdom") or "").lower()
                    if not sci or rank not in ["SPECIES", "SUBSPECIES", "GENUS"]:
                        continue
                    if kingdom in ["viruses", "bacteria", "archaea", "viroids"] or any(v in sci.lower() for v in ["virus", "circovirus", "astrovirus", "phage"]):
                        continue

                    key = sci.strip().lower()
                    if key not in results_map:
                        vernacular = item.get("vernacularName")
                        cat = classify_category(
                            kingdom=item.get("kingdom"),
                            phylum=item.get("phylum"),
                            class_name=item.get("class"),
                            order=item.get("order"),
                            family=item.get("family"),
                            canonical_name=sci
                        )
                        results_map[key] = {
                            "id": None,
                            "scientific_name": sci.strip(),
                            "common_name": vernacular.title() if vernacular else None,
                            "category": cat
                        }
        except Exception as s_err:
            print(f"[SpeciesSearch] GBIF Suggest API exception for '{clean_q}': {s_err}")

        # 2B. GBIF Global Search API
        try:
            resp = session.get(
                GBIF_SEARCH_URL,
                params={"q": clean_q, "limit": 30},
                headers=HTTP_HEADERS,
                timeout=5.0
            )
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("results", []):
                    sci = item.get("canonicalName") or item.get("species") or item.get("scientificName")
                    rank = (item.get("rank") or "").upper()
                    kingdom = (item.get("kingdom") or "").lower()
                    
                    # Filter non-biological entities (viruses, bacteria, astroviruses, etc.)
                    if not sci or rank not in ["SPECIES", "SUBSPECIES", "GENUS", "FAMILY"]:
                        continue
                    if kingdom in ["viruses", "bacteria", "archaea", "viroids"] or any(v in sci.lower() for v in ["virus", "circovirus", "astrovirus", "phage"]):
                        continue
                        
                    key = sci.strip().lower()
                    if key not in results_map:
                        vernacular = item.get("vernacularName")
                        if not vernacular and item.get("vernacularNames"):
                            for v in item["vernacularNames"]:
                                if v.get("language") in ["eng", "en", None]:
                                    vernacular = v.get("vernacularName")
                                    break
                        
                        cat = classify_category(
                            kingdom=item.get("kingdom"),
                            phylum=item.get("phylum"),
                            class_name=item.get("class"),
                            order=item.get("order"),
                            family=item.get("family"),
                            canonical_name=sci
                        )

                        results_map[key] = {
                            "id": None,
                            "scientific_name": sci.strip(),
                            "common_name": vernacular.title() if vernacular else None,
                            "category": cat
                        }
            else:
                api_error_occurred = True
        except Exception as e:
            print(f"[SpeciesSearch] GBIF API exception for '{clean_q}': {e}")
            api_error_occurred = True

        # 3. Wikipedia API fallback if GBIF yielded 0 results for a common name
        if not results_map:
            try:
                w_resp = session.get(
                    WIKIPEDIA_SEARCH_URL,
                    params={"action": "query", "list": "search", "srsearch": f"{clean_q} species", "format": "json"},
                    headers=HTTP_HEADERS,
                    timeout=4.0
                )
                if w_resp.status_code == 200:
                    w_hits = w_resp.json().get("query", {}).get("search", [])[:3]
                    for hit in w_hits:
                        title = hit["title"]
                        m_resp = session.get(GBIF_MATCH_URL, params={"name": title}, headers=HTTP_HEADERS, timeout=3.0)
                        if m_resp.status_code == 200:
                            mdata = m_resp.json()
                            sci = mdata.get("canonicalName") or mdata.get("scientificName")
                            m_kingdom = (mdata.get("kingdom") or "").lower()
                            if sci and mdata.get("rank") in ["SPECIES", "SUBSPECIES", "GENUS"] and m_kingdom not in ["viruses", "bacteria"]:
                                key = sci.strip().lower()
                                if key not in results_map:
                                    cat = classify_category(
                                        kingdom=mdata.get("kingdom"),
                                        phylum=mdata.get("phylum"),
                                        class_name=mdata.get("class"),
                                        order=mdata.get("order"),
                                        family=mdata.get("family"),
                                        canonical_name=sci
                                    )
                                    results_map[key] = {
                                        "id": None,
                                        "scientific_name": sci.strip(),
                                        "common_name": title,
                                        "category": cat
                                    }
            except Exception as w_err:
                print(f"[SpeciesSearch] Wikipedia API exception for '{clean_q}': {w_err}")
                api_error_occurred = True

    # 4. If query is empty and no local results, populate with default showcase species
    if not results_map and not clean_q:
        for default_sp in DEFAULT_GLOBAL_SPECIES:
            key = default_sp["scientific_name"].lower()
            results_map[key] = {
                "id": None,
                "scientific_name": default_sp["scientific_name"],
                "common_name": default_sp["common_name"],
                "category": default_sp["category"]
            }

    # If query was provided, no local or global results were found, and an API error occurred:
    if clean_q and not results_map and api_error_occurred:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Species search is temporarily unavailable. Please try again."
        )

    # 5. Score & Rank results by relevance to query clean_q
    scored_items = []
    q_lower = clean_q.lower()

    for key, sp_info in results_map.items():
        sci_name = sp_info["scientific_name"]
        comm_name = sp_info.get("common_name") or ""
        cat = sp_info["category"]
        
        # Check category filter
        if category and not _category_matches(cat, category):
            continue

        score = 0
        sci_lower = sci_name.lower()
        comm_lower = comm_name.lower()

        if q_lower:
            if comm_lower == q_lower:
                score += 1000
            elif comm_lower.startswith(q_lower):
                score += 800
            elif f" {q_lower} " in f" {comm_lower} " or comm_lower.endswith(q_lower):
                score += 600
            elif q_lower in comm_lower:
                score += 400

            if sci_lower == q_lower:
                score += 900
            elif sci_lower.startswith(q_lower):
                score += 700
            elif q_lower in sci_lower:
                score += 500
        else:
            score = 100

        scored_items.append((score, sp_info))

    # Sort descending by score
    scored_items.sort(key=lambda x: x[0], reverse=True)

    from concurrent.futures import ThreadPoolExecutor

    top_candidates = [sp_info for score, sp_info in scored_items[:12]]
    
    def _enrich_single(sp_info):
        sci = sp_info["scientific_name"]
        cat = sp_info["category"]
        comm = sp_info.get("common_name")
        prof = SpeciesEnrichmentService.get_species_profile(sci, common_name=comm, category=cat)
        return (sp_info, prof)

    with ThreadPoolExecutor(max_workers=5) as executor:
        enriched_list = list(executor.map(_enrich_single, top_candidates))

    final_results = []
    
    for sp_info, profile in enriched_list:
        sci_name = sp_info["scientific_name"]
        cat = sp_info["category"]

        # Check observation count in local DB
        count = db.query(func.count(Observation.id)).filter(
            Observation.scientific_name.ilike(sci_name)
        ).scalar() or 0
        
        last_obs = db.query(func.max(Observation.observation_date)).filter(
            Observation.scientific_name.ilike(sci_name)
        ).scalar()

        # Refine category using taxonomy from profile if available
        if profile and profile.taxonomy:
            cat = classify_category(
                kingdom=profile.taxonomy.kingdom,
                phylum=profile.taxonomy.phylum,
                class_name=profile.taxonomy.class_name,
                order=profile.taxonomy.order,
                family=profile.taxonomy.family,
                canonical_name=sci_name
            )

        ref_images = [img.model_dump() for img in profile.reference_images] if profile and profile.reference_images else []
        facts = profile.facts if profile else None

        final_results.append(
            SpeciesResponse(
                id=sp_info.get("id"),
                scientific_name=sci_name,
                common_name=profile.common_name or sp_info.get("common_name") or sci_name,
                category=cat,
                taxonomic_rank=profile.taxonomy.rank if profile and profile.taxonomy else "Species",
                kingdom=profile.taxonomy.kingdom if profile and profile.taxonomy else None,
                phylum=profile.taxonomy.phylum if profile and profile.taxonomy else None,
                class_name=profile.taxonomy.class_name if profile and profile.taxonomy else None,
                order=profile.taxonomy.order if profile and profile.taxonomy else None,
                family=profile.taxonomy.family if profile and profile.taxonomy else None,
                genus=profile.taxonomy.genus if profile and profile.taxonomy else None,
                description=profile.description if profile else None,
                habitat=facts.habitat if facts and facts.habitat else "Information unavailable",
                diet=facts.diet if facts and facts.diet else "Information unavailable",
                behavior=facts.behavior if facts and facts.behavior else "Information unavailable",
                reproduction=facts.reproduction if facts and facts.reproduction else "Information unavailable",
                conservation=facts.conservation or facts.conservation_status if facts and (facts.conservation or facts.conservation_status) else "Information unavailable",
                reference_images=ref_images,
                observation_count=count,
                last_observed=last_obs
            )
        )

    return final_results


@router.get("/profile", response_model=SpeciesResponse)
def get_species_profile_by_name(
    scientific_name: str = Query(..., description="Scientific name of species"),
    common_name: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    count = db.query(func.count(Observation.id)).filter(
        Observation.scientific_name.ilike(scientific_name)
    ).scalar() or 0
    
    last_obs = db.query(func.max(Observation.observation_date)).filter(
        Observation.scientific_name.ilike(scientific_name)
    ).scalar()

    profile = SpeciesEnrichmentService.get_species_profile(
        scientific_name, common_name=common_name, category=category
    )
    
    final_cat = category or "other"
    if profile and profile.taxonomy:
        final_cat = classify_category(
            kingdom=profile.taxonomy.kingdom,
            phylum=profile.taxonomy.phylum,
            class_name=profile.taxonomy.class_name,
            order=profile.taxonomy.order,
            family=profile.taxonomy.family,
            canonical_name=scientific_name
        )

    ref_images = [img.model_dump() for img in profile.reference_images] if profile and profile.reference_images else []
    facts = profile.facts if profile else None

    return SpeciesResponse(
        id=None,
        scientific_name=scientific_name,
        common_name=profile.common_name or common_name or scientific_name,
        category=final_cat,
        taxonomic_rank=profile.taxonomy.rank if profile and profile.taxonomy else "Species",
        kingdom=profile.taxonomy.kingdom if profile and profile.taxonomy else None,
        phylum=profile.taxonomy.phylum if profile and profile.taxonomy else None,
        class_name=profile.taxonomy.class_name if profile and profile.taxonomy else None,
        order=profile.taxonomy.order if profile and profile.taxonomy else None,
        family=profile.taxonomy.family if profile and profile.taxonomy else None,
        genus=profile.taxonomy.genus if profile and profile.taxonomy else None,
        description=profile.description if profile else None,
        habitat=facts.habitat if facts and facts.habitat else "Information unavailable",
        diet=facts.diet if facts and facts.diet else "Information unavailable",
        behavior=facts.behavior if facts and facts.behavior else "Information unavailable",
        reproduction=facts.reproduction if facts and facts.reproduction else "Information unavailable",
        conservation=facts.conservation or facts.conservation_status if facts and (facts.conservation or facts.conservation_status) else "Information unavailable",
        reference_images=ref_images,
        observation_count=count,
        last_observed=last_obs
    )
