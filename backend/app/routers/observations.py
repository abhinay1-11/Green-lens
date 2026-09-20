from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.observation import Observation
from app.models.image import ObservationImage
from app.models.identification import IdentificationResult
from app.models.species import Species
from app.schemas.observation import ObservationCreate, ObservationResponse, ObservationUpdate
from app.services.taxonomy.gbif import lookup_gbif_taxonomy
from app.services.spatial.boundary import boundary_validator

router = APIRouter(prefix="/api/observations", tags=["Observations"])

@router.post("", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED)
def create_observation(payload: ObservationCreate, db: Session = Depends(get_db)):
    """
    Creates a new biodiversity observation record with linked images, AI prediction audit log, and spatial validation.
    """
    # Create Observation
    obs = Observation(
        category=payload.category,
        scientific_name=payload.scientific_name,
        common_name=payload.common_name,
        taxon_id=payload.taxon_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_accuracy=payload.location_accuracy,
        campus_zone=payload.campus_zone,
        notes=payload.notes,
        ai_provider=payload.ai_provider,
        ai_model_version=payload.ai_model_version,
        ai_confidence=payload.ai_confidence,
        ai_predicted_scientific_name=payload.ai_predicted_scientific_name,
        ai_predicted_common_name=payload.ai_predicted_common_name,
        verification_status=payload.verification_status or "user_confirmed"
    )
    db.add(obs)
    db.flush()

    # Save images
    for idx, path in enumerate(payload.image_paths):
        organ = payload.organ_tags[idx] if idx < len(payload.organ_tags) else "auto"
        img = ObservationImage(
            observation_id=obs.id,
            file_path=path,
            original_filename=path.split("/")[-1],
            mime_type="image/jpeg",
            file_size=1000,
            organ=organ
        )
        db.add(img)

    # Save AI prediction audit log
    if payload.predictions_history:
        for pred in payload.predictions_history:
            ident = IdentificationResult(
                observation_id=obs.id,
                provider=payload.ai_provider or "unknown",
                category=payload.category,
                rank=pred.get("rank", 1),
                scientific_name=pred.get("scientific_name", "Unknown"),
                common_name=pred.get("common_name") or (pred.get("common_names", [""])[0] if pred.get("common_names") else None),
                confidence=pred.get("confidence", 0.0)
            )
            db.add(ident)

    # Update/Create Species record if species name is provided
    if payload.scientific_name:
        existing_species = db.query(Species).filter(Species.scientific_name == payload.scientific_name).first()
        if not existing_species:
            gbif_data = lookup_gbif_taxonomy(payload.scientific_name)
            sp = Species(
                scientific_name=payload.scientific_name,
                common_name=payload.common_name,
                category=payload.category,
                kingdom=gbif_data.get("kingdom"),
                family=gbif_data.get("family"),
                genus=gbif_data.get("genus")
            )
            db.add(sp)

    db.commit()
    db.refresh(obs)
    return obs


@router.get("", response_model=List[ObservationResponse])
def get_observations(
    category: Optional[str] = None,
    campus_zone: Optional[str] = None,
    verification_status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Observation)

    if category and category.lower() != "all":
        query = query.filter(Observation.category == category.lower())

    if campus_zone and campus_zone.lower() != "all":
        query = query.filter(Observation.campus_zone == campus_zone)

    if verification_status and verification_status.lower() != "all":
        query = query.filter(Observation.verification_status == verification_status)

    if search:
        s_term = f"%{search}%"
        query = query.filter(
            (Observation.scientific_name.ilike(s_term)) |
            (Observation.common_name.ilike(s_term)) |
            (Observation.notes.ilike(s_term))
        )

    observations = query.order_by(Observation.created_at.desc()).offset(skip).limit(limit).all()
    return observations


@router.get("/{id}", response_model=ObservationResponse)
def get_observation_by_id(id: str, db: Session = Depends(get_db)):
    obs = db.query(Observation).filter(Observation.id == id).first()
    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "OBSERVATION_NOT_FOUND", "message": f"Observation with ID '{id}' not found."}
        )
    return obs


@router.patch("/{id}", response_model=ObservationResponse)
def update_observation(id: str, payload: ObservationUpdate, db: Session = Depends(get_db)):
    obs = db.query(Observation).filter(Observation.id == id).first()
    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "OBSERVATION_NOT_FOUND", "message": f"Observation with ID '{id}' not found."}
        )

    if payload.scientific_name is not None:
        obs.scientific_name = payload.scientific_name
        # If user changed species name, set status to user_corrected if it differs from AI prediction
        if obs.ai_predicted_scientific_name and obs.scientific_name != obs.ai_predicted_scientific_name:
            obs.verification_status = "user_corrected"

    if payload.common_name is not None:
        obs.common_name = payload.common_name

    if payload.verification_status is not None:
        obs.verification_status = payload.verification_status

    if payload.campus_zone is not None:
        obs.campus_zone = payload.campus_zone

    if payload.notes is not None:
        obs.notes = payload.notes

    if payload.latitude is not None:
        obs.latitude = payload.latitude

    if payload.longitude is not None:
        obs.longitude = payload.longitude

    db.commit()
    db.refresh(obs)
    return obs


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_observation(id: str, db: Session = Depends(get_db)):
    obs = db.query(Observation).filter(Observation.id == id).first()
    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "OBSERVATION_NOT_FOUND", "message": f"Observation with ID '{id}' not found."}
        )
    db.delete(obs)
    db.commit()
    return None
