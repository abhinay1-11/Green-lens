import pytest
from unittest.mock import patch, MagicMock
from app.services.species_enrichment import SpeciesEnrichmentService, SpeciesProfile, SpeciesTaxonomy, SpeciesFacts, ReferenceImage
from app.services.species_enrichment.gbif_provider import fetch_gbif_species_data
from app.services.species_enrichment.wikipedia_provider import fetch_wikipedia_species_data
from app.services.species_enrichment.cache import get_cached_species_profile, set_cached_species_profile

def test_gbif_provider_success():
    mock_match_response = MagicMock()
    mock_match_response.status_code = 200
    mock_match_response.json.return_value = {
        "matchType": "EXACT",
        "usageKey": 2473461,
        "scientificName": "Centrocercus urophasianus (Bonaparte, 1827)",
        "canonicalName": "Centrocercus urophasianus",
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Aves",
        "order": "Galliformes",
        "family": "Phasianidae",
        "genus": "Centrocercus",
        "species": "Centrocercus urophasianus"
    }

    mock_media_response = MagicMock()
    mock_media_response.status_code = 200
    mock_media_response.json.return_value = {
        "results": [
            {
                "type": "StillImage",
                "identifier": "https://images.gbif.org/sample1.jpg",
                "creator": "Audubon Society",
                "license": "http://creativecommons.org/licenses/by/4.0/",
                "references": "https://gbif.org/occurrence/123"
            }
        ]
    }

    mock_desc_response = MagicMock()
    mock_desc_response.status_code = 200
    mock_desc_response.json.return_value = {
        "results": [
            {"description": "Large grouse species native to sagebrush country in western North America."}
        ]
    }

    def mocked_requests_get(url, **kwargs):
        if "species/match" in url:
            return mock_match_response
        elif "media" in url:
            return mock_media_response
        elif "descriptions" in url:
            return mock_desc_response
        return MagicMock(status_code=404)

    mock_session = MagicMock()
    mock_session.get.side_effect = mocked_requests_get

    with patch("app.services.species_enrichment.gbif_provider.get_http_session", return_value=mock_session):
        data = fetch_gbif_species_data("Centrocercus urophasianus")
        assert data["taxonomy"] is not None
        assert data["taxonomy"].kingdom == "Animalia"
        assert len(data["reference_images"]) == 1
        assert data["reference_images"][0].creator == "Audubon Society"
        assert "sagebrush" in data["description"]

def test_wikipedia_provider_success():
    mock_wiki_resp = MagicMock()
    mock_wiki_resp.status_code = 200
    mock_wiki_resp.json.return_value = {
        "type": "standard",
        "extract": "The Greater Sage-Grouse (Centrocercus urophasianus) is a large bird species in the grouse family. It inhabits sagebrush plains. It feeds on sagebrush leaves and seeds. It breeds in leks during spring. It is listed as near threatened.",
        "originalimage": {"source": "https://upload.wikimedia.org/sage_grouse.jpg"},
        "thumbnail": {"source": "https://upload.wikimedia.org/sage_grouse_thumb.jpg"}
    }
    mock_session = MagicMock()
    mock_session.get.return_value = mock_wiki_resp

    with patch("app.services.species_enrichment.wikipedia_provider.get_http_session", return_value=mock_session):
        data = fetch_wikipedia_species_data("Centrocercus urophasianus", "Greater Sage-Grouse")
        assert "grouse" in data["description"].lower()
        assert len(data["reference_images"]) == 1
        assert data["facts"].habitat is not None
        assert data["facts"].diet is not None

def test_cache_set_and_get():
    test_name = "test_species_cache_spec_123"
    profile_data = {
        "available": True,
        "scientific_name": test_name,
        "common_name": "Test Species",
        "description": "Cache test description",
        "taxonomy": {"kingdom": "Animalia", "species": test_name},
        "facts": {"habitat": "Test Habitat"},
        "reference_images": [{"url": "https://test.com/img.jpg", "source": "Test", "creator": "Tester"}],
        "sources": ["Unit Test Cache"]
    }

    set_cached_species_profile(test_name, profile_data)
    cached = get_cached_species_profile(test_name)
    assert cached is not None
    assert cached["common_name"] == "Test Species"
    assert cached["description"] == "Cache test description"

def test_enrichment_service_handles_timeouts_gracefully():
    with patch("requests.get", side_effect=Exception("Connection Timeout")):
        profile = SpeciesEnrichmentService.get_species_profile("Timeout species test")
        assert profile is not None
        assert profile.scientific_name == "Timeout species test"
        # Should return safely without crashing
        assert profile.available is False

def test_no_secret_leakage_in_profile():
    profile = SpeciesEnrichmentService.get_species_profile("Centrocercus urophasianus")
    profile_json = str(profile.model_dump())
    assert "HF_TOKEN" not in profile_json
    assert "api_key" not in profile_json.lower()
