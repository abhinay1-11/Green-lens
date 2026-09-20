from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.database import get_db
from app.models.observation import Observation
from app.schemas.analytics import DashboardMetrics, SpeciesFrequency, ZoneActivity

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """
    Returns real-time database calculated biodiversity metrics. No hardcoded numbers.
    """
    total_obs = db.query(func.count(Observation.id)).scalar() or 0
    unique_sp = db.query(func.count(func.distinct(Observation.scientific_name))).filter(Observation.scientific_name.isnot(None)).scalar() or 0
    
    plants = db.query(func.count(Observation.id)).filter(Observation.category == "plant").scalar() or 0
    birds = db.query(func.count(Observation.id)).filter(Observation.category == "bird").scalar() or 0
    insects = db.query(func.count(Observation.id)).filter(Observation.category == "insect").scalar() or 0
    unknown = db.query(func.count(Observation.id)).filter(Observation.category == "unknown").scalar() or 0
    
    confirmed = db.query(func.count(Observation.id)).filter(
        Observation.verification_status.in_(["user_confirmed", "user_corrected", "expert_verified"])
    ).scalar() or 0

    pending = db.query(func.count(Observation.id)).filter(
        Observation.verification_status.in_(["pending", "ai_suggested"])
    ).scalar() or 0

    return DashboardMetrics(
        total_observations=total_obs,
        unique_species=unique_sp,
        plants_count=plants,
        birds_count=birds,
        insects_count=insects,
        unknown_count=unknown,
        confirmed_count=confirmed,
        pending_count=pending
    )


@router.get("/trends")
def get_trend_analytics(period: str = "30d", db: Session = Depends(get_db)):
    """
    Returns top species ranking, campus zone activity, and category time-series trend data.
    """
    # 1. Top Species frequency
    top_sp_query = db.query(
        Observation.scientific_name,
        Observation.common_name,
        Observation.category,
        func.count(Observation.id).label("count")
    ).filter(Observation.scientific_name.isnot(None))\
     .group_by(Observation.scientific_name)\
     .order_by(func.count(Observation.id).desc())\
     .limit(10).all()

    top_species = [
        {
            "scientific_name": item[0],
            "common_name": item[1],
            "category": item[2],
            "count": item[3]
        }
        for item in top_sp_query
    ]

    # 2. Zone distribution
    zone_query = db.query(
        Observation.campus_zone,
        func.count(Observation.id).label("count")
    ).filter(Observation.campus_zone.isnot(None))\
     .group_by(Observation.campus_zone)\
     .order_by(func.count(Observation.id).desc()).all()

    zone_activity = [{"zone": item[0], "count": item[1]} for item in zone_query]

    # 3. Monthly/Weekly time series simulation based on DB records
    days = 30 if period == "30d" else (90 if period == "90d" else 365)
    start_date = datetime.utcnow() - timedelta(days=days)

    trend_points = []
    for i in range(7):
        d_start = start_date + timedelta(days=i * (days // 7))
        d_end = d_start + timedelta(days=days // 7)
        label = d_start.strftime("%b %d")

        p_cnt = db.query(func.count(Observation.id)).filter(Observation.category == "plant", Observation.created_at >= d_start, Observation.created_at < d_end).scalar() or 0
        b_cnt = db.query(func.count(Observation.id)).filter(Observation.category == "bird", Observation.created_at >= d_start, Observation.created_at < d_end).scalar() or 0
        i_cnt = db.query(func.count(Observation.id)).filter(Observation.category == "insect", Observation.created_at >= d_start, Observation.created_at < d_end).scalar() or 0

        trend_points.append({
            "date": label,
            "plants": p_cnt,
            "birds": b_cnt,
            "insects": i_cnt,
            "total": p_cnt + b_cnt + i_cnt
        })

    return {
        "top_species": top_species,
        "zone_activity": zone_activity,
        "trend_points": trend_points
    }


@router.get("/map")
def get_map_observations(
    category: str = "all",
    campus_zone: str = "all",
    verification_status: str = "all",
    db: Session = Depends(get_db)
):
    """
    Returns observations formatted as GeoJSON FeatureCollection for Leaflet map markers.
    """
    query = db.query(Observation).filter(
        Observation.latitude.isnot(None),
        Observation.longitude.isnot(None)
    )

    if category != "all":
        query = query.filter(Observation.category == category.lower())

    if campus_zone != "all":
        query = query.filter(Observation.campus_zone == campus_zone)

    if verification_status != "all":
        query = query.filter(Observation.verification_status == verification_status)

    observations = query.all()
    features = []

    for obs in observations:
        primary_image = obs.images[0].file_path if obs.images else None
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [obs.longitude, obs.latitude]
            },
            "properties": {
                "id": obs.id,
                "category": obs.category,
                "scientific_name": obs.scientific_name or "Unidentified",
                "common_name": obs.common_name or "",
                "confidence": obs.ai_confidence,
                "provider": obs.ai_provider or "N/A",
                "verification_status": obs.verification_status,
                "campus_zone": obs.campus_zone or "General Campus",
                "observation_date": obs.observation_date.strftime("%Y-%m-%d %H:%M"),
                "image_url": primary_image
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }
