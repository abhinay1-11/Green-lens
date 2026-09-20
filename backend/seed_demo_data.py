"""
Seed script for populating GreenLens SQLite database with initial campus biodiversity observations.
"""
from datetime import datetime, timedelta
from app.database import SessionLocal, Base, engine
from app.models.observation import Observation
from app.models.image import ObservationImage
from app.models.identification import IdentificationResult
from app.models.species import Species

# Ensure DB tables exist
Base.metadata.create_all(bind=engine)

def seed_database():
    db = SessionLocal()

    # Clear existing data if any
    db.query(IdentificationResult).delete()
    db.query(ObservationImage).delete()
    db.query(Observation).delete()
    db.query(Species).delete()

    # 1. Seed Species
    species_data = [
        {"scientific": "Azadirachta indica", "common": "Neem Tree", "cat": "plant", "fam": "Meliaceae", "gen": "Azadirachta"},
        {"scientific": "Mangifera indica", "common": "Mango Tree", "cat": "plant", "fam": "Anacardiaceae", "gen": "Mangifera"},
        {"scientific": "Ficus religiosa", "common": "Sacred Fig (Peepal)", "cat": "plant", "fam": "Moraceae", "gen": "Ficus"},
        {"scientific": "Passer domesticus", "common": "House Sparrow", "cat": "bird", "fam": "Passeridae", "gen": "Passer"},
        {"scientific": "Acridotheres tristis", "common": "Common Myna", "cat": "bird", "fam": "Sturnidae", "gen": "Acridotheres"},
        {"scientific": "Pycnonotus cafer", "common": "Red-vented Bulbul", "cat": "bird", "fam": "Pycnonotidae", "gen": "Pycnonotus"},
        {"scientific": "Apis cerana", "common": "Asian Honey Bee", "cat": "insect", "fam": "Apidae", "gen": "Apis"},
        {"scientific": "Danaus chrysippus", "common": "Plain Tiger Butterfly", "cat": "insect", "fam": "Nymphalidae", "gen": "Danaus"},
        {"scientific": "Coccinella septempunctata", "common": "Seven-spot Ladybird", "cat": "insect", "fam": "Coccinellidae", "gen": "Coccinella"}
    ]

    for item in species_data:
        sp = Species(
            scientific_name=item["scientific"],
            common_name=item["common"],
            category=item["cat"],
            kingdom="Plantae" if item["cat"] == "plant" else "Animalia",
            family=item["fam"],
            genus=item["gen"]
        )
        db.add(sp)

    # 2. Seed Observations
    obs_list = [
        {
            "cat": "plant",
            "scientific": "Azadirachta indica",
            "common": "Neem Tree",
            "lat": 12.9745,
            "lon": 77.5890,
            "zone": "botanical_garden",
            "conf": 0.91,
            "status": "user_confirmed",
            "provider": "plantnet",
            "days_ago": 1,
            "notes": "Healthy mature neem tree near botanical garden entrance."
        },
        {
            "cat": "plant",
            "scientific": "Mangifera indica",
            "common": "Mango Tree",
            "lat": 12.9760,
            "lon": 77.5920,
            "zone": "academic_block",
            "conf": 0.88,
            "status": "user_confirmed",
            "provider": "plantnet",
            "days_ago": 3,
            "notes": "Flowering mango tree in front of academic block courtyard."
        },
        {
            "cat": "plant",
            "scientific": "Ficus religiosa",
            "common": "Sacred Fig (Peepal)",
            "lat": 12.9720,
            "lon": 77.5880,
            "zone": "library_quad",
            "conf": 0.95,
            "status": "expert_verified",
            "provider": "plantnet",
            "days_ago": 5,
            "notes": "Ancient Peepal tree shade canopy near central library."
        },
        {
            "cat": "bird",
            "scientific": "Passer domesticus",
            "common": "House Sparrow",
            "lat": 12.9735,
            "lon": 77.5940,
            "zone": "hostel_grounds",
            "conf": 0.89,
            "status": "user_confirmed",
            "provider": "birdnet",
            "days_ago": 2,
            "notes": "Flock of sparrows nesting in student residential quad hedges."
        },
        {
            "cat": "bird",
            "scientific": "Pycnonotus cafer",
            "common": "Red-vented Bulbul",
            "lat": 12.9770,
            "lon": 77.5910,
            "zone": "lake_pond",
            "conf": 0.82,
            "status": "user_confirmed",
            "provider": "birdnet",
            "days_ago": 4,
            "notes": "Sighted perched on wetland reeds near campus lake."
        },
        {
            "cat": "insect",
            "scientific": "Apis cerana",
            "common": "Asian Honey Bee",
            "lat": 12.9750,
            "lon": 77.5895,
            "zone": "botanical_garden",
            "conf": 0.85,
            "status": "user_confirmed",
            "provider": "insect-ai",
            "days_ago": 2,
            "notes": "Active foraging on neem flowers."
        },
        {
            "cat": "insect",
            "scientific": "Danaus chrysippus",
            "common": "Plain Tiger Butterfly",
            "lat": 12.9765,
            "lon": 77.5935,
            "zone": "cafeteria_plaza",
            "conf": 0.93,
            "status": "user_confirmed",
            "provider": "insect-ai",
            "days_ago": 6,
            "notes": "Butterfly fluttering near cafeteria floral beds."
        }
    ]

    for data in obs_list:
        date_obs = datetime.utcnow() - timedelta(days=data["days_ago"])
        obs = Observation(
            category=data["cat"],
            scientific_name=data["scientific"],
            common_name=data["common"],
            latitude=data["lat"],
            longitude=data["lon"],
            campus_zone=data["zone"],
            ai_provider=data["provider"],
            ai_model_version="v1.0.0",
            ai_confidence=data["conf"],
            ai_predicted_scientific_name=data["scientific"],
            ai_predicted_common_name=data["common"],
            verification_status=data["status"],
            notes=data["notes"],
            observation_date=date_obs,
            created_at=date_obs
        )
        db.add(obs)
        db.flush()

        # Add image link
        img = ObservationImage(
            observation_id=obs.id,
            file_path="https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=600",
            original_filename="sample_observation.jpg",
            mime_type="image/jpeg",
            file_size=204800,
            organ="auto"
        )
        db.add(img)

        # Add AI audit history
        ident = IdentificationResult(
            observation_id=obs.id,
            provider=data["provider"],
            category=data["cat"],
            rank=1,
            scientific_name=data["scientific"],
            common_name=data["common"],
            confidence=data["conf"]
        )
        db.add(ident)

    db.commit()
    db.close()
    print("Successfully seeded demo campus biodiversity observations!")

if __name__ == "__main__":
    seed_database()
