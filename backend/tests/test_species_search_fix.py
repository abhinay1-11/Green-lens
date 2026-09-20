import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_species_search.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_species_search_all_required_queries():
    queries = [
        "Greater Sage-Grouse",
        "Neem",
        "Apis mellifera",
        "Black-footed Albatross",
        "Monarch Butterfly",
        "Centrocercus urophasianus",
        "Azadirachta indica"
    ]
    
    for q in queries:
        resp = client.get("/api/species/search", params={"q": q, "category": "ALL"})
        assert resp.status_code == 200, f"Search failed for query '{q}': {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0, f"Search returned empty result for query '{q}'"
        
        first = data[0]
        assert "scientific_name" in first
        assert "common_name" in first
        assert "category" in first


def test_species_search_category_filtering():
    resp_birds = client.get("/api/species/search", params={"q": "Greater Sage-Grouse", "category": "BIRDS"})
    assert resp_birds.status_code == 200
    for sp in resp_birds.json():
        assert sp["category"].lower() in ["bird", "other"]

    resp_plants = client.get("/api/species/search", params={"q": "Neem", "category": "PLANTS"})
    assert resp_plants.status_code == 200
    for sp in resp_plants.json():
        assert sp["category"].lower() in ["plant", "tree", "flower", "other"]


def test_species_profile_endpoint():
    resp = client.get("/api/species/profile", params={"scientific_name": "Centrocercus urophasianus", "common_name": "Greater Sage-Grouse", "category": "bird"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["scientific_name"] == "Centrocercus urophasianus"
    assert data["common_name"] is not None
    assert "observation_count" in data
