import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.database import SessionLocal
from app.models.observation import Observation
from app.models.collection import Collection, CollectionItem

client = TestClient(app)


def test_collections_full_lifecycle():
    # 0. Setup test observation in database
    db = SessionLocal()
    test_obs_id = "test-obs-lifecycle-999"
    existing_obs = db.query(Observation).filter(Observation.id == test_obs_id).first()
    if not existing_obs:
        obs = Observation(
            id=test_obs_id,
            category="bird",
            scientific_name="Turdus migratorius",
            common_name="American Robin",
            observation_date=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(obs)
        db.commit()
    db.close()

    # 1. POST /api/collections -> Create collection
    create_payload = {
        "name": "Lifecycle Test Collection",
        "description": "A collection for automated integration testing"
    }
    res = client.post("/api/collections", json=create_payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert "id" in data
    coll_id = data["id"]
    assert data["name"] == "Lifecycle Test Collection"

    # 2. GET /api/collections -> List collections
    res_list = client.get("/api/collections")
    assert res_list.status_code == 200
    collections = res_list.json()
    assert any(c["id"] == coll_id for c in collections)

    # 3. GET /api/collections/{id} -> Get collection detail
    res_detail = client.get(f"/api/collections/{coll_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == coll_id

    # 4. Add species item to collection
    species_item_payload = {
        "item_type": "explored",
        "scientific_name": "Danaus plexippus",
        "common_name": "Monarch Butterfly",
        "category": "insect"
    }
    res_item1 = client.post(f"/api/collections/{coll_id}/items", json=species_item_payload)
    assert res_item1.status_code == 201
    item1_data = res_item1.json()
    item1_id = item1_data["id"]
    assert item1_data["scientific_name"] == "Danaus plexippus"

    # 5. Add observation item to collection
    obs_item_payload = {
        "item_type": "observation",
        "scientific_name": "Turdus migratorius",
        "common_name": "American Robin",
        "category": "bird",
        "observation_id": test_obs_id
    }
    res_item2 = client.post(f"/api/collections/{coll_id}/items", json=obs_item_payload)
    assert res_item2.status_code == 201
    item2_data = res_item2.json()
    item2_id = item2_data["id"]

    # 6. GET collection detail -> Verify counts and enriched items
    res_detail2 = client.get(f"/api/collections/{coll_id}")
    assert res_detail2.status_code == 200
    detail2 = res_detail2.json()
    assert detail2["species_count"] == 2
    assert detail2["observation_count"] == 1
    assert len(detail2["items"]) == 2

    # 7. PUT /api/collections/{id} -> Update collection details
    update_payload = {
        "name": "Updated Lifecycle Collection",
        "description": "Updated description"
    }
    res_update = client.put(f"/api/collections/{coll_id}", json=update_payload)
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Updated Lifecycle Collection"

    # 8. DELETE collection item
    res_del_item = client.delete(f"/api/collections/{coll_id}/items/{item1_id}")
    assert res_del_item.status_code == 204

    # Verify item is removed
    res_detail3 = client.get(f"/api/collections/{coll_id}")
    assert len(res_detail3.json()["items"]) == 1

    # 9. DELETE collection
    res_del_coll = client.delete(f"/api/collections/{coll_id}")
    assert res_del_coll.status_code == 204

    # Verify collection 404
    res_get_deleted = client.get(f"/api/collections/{coll_id}")
    assert res_get_deleted.status_code == 404

    # 10. Verify original observation still exists in DB
    db2 = SessionLocal()
    obs_after = db2.query(Observation).filter(Observation.id == test_obs_id).first()
    assert obs_after is not None, "Original observation was accidentally deleted!"
    db2.close()


def test_collections_validation():
    # Empty name validation
    res = client.post("/api/collections", json={"name": "   ", "description": "Test"})
    assert res.status_code in (400, 422)

    # Missing name validation
    res_missing = client.post("/api/collections", json={"description": "Test"})
    assert res_missing.status_code == 422
