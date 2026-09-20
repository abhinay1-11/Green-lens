import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_collections.db"
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
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

client = TestClient(app)

def test_collections_crud_workflow():
    # 1. Create collection
    resp = client.post("/api/collections", json={
        "name": "My Bird Collection",
        "description": "Bird species identified on campus"
    })
    assert resp.status_code == 201
    coll_data = resp.json()
    assert coll_data["name"] == "My Bird Collection"
    coll_id = coll_data["id"]

    # 2. Add explored item
    resp = client.post(f"/api/collections/{coll_id}/items", json={
        "item_type": "explored",
        "scientific_name": "Centrocercus urophasianus",
        "common_name": "Greater Sage-Grouse",
        "category": "bird"
    })
    assert resp.status_code == 201
    item_data = resp.json()
    assert item_data["scientific_name"] == "Centrocercus urophasianus"

    # 3. Get collection detail
    resp = client.get(f"/api/collections/{coll_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["species_count"] == 1
    assert len(detail["items"]) == 1

    # 4. CSV export
    resp = client.get(f"/api/collections/{coll_id}/export/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "Centrocercus urophasianus" in resp.text

    # 5. PDF export
    resp = client.get(f"/api/collections/{coll_id}/export/pdf")
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers["content-type"]
    assert len(resp.content) > 100

    # 6. Delete collection
    resp = client.delete(f"/api/collections/{coll_id}")
    assert resp.status_code == 204
