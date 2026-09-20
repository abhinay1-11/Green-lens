from fastapi import APIRouter, Depends, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.observation import Observation
from app.services.reports.csv_exporter import generate_observations_csv
from app.services.reports.pdf_exporter import generate_observations_html_report

router = APIRouter(prefix="/api/reports", tags=["Reports & Export"])

@router.get("/observations.csv")
def download_observations_csv(db: Session = Depends(get_db)):
    """
    Exports all recorded campus observations as CSV file.
    """
    observations = db.query(Observation).order_by(Observation.observation_date.desc()).all()
    csv_content = generate_observations_csv(observations)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=greenlens_observations_export.csv"
        }
    )


@router.get("/observations.pdf", response_class=HTMLResponse)
def download_observations_pdf(db: Session = Depends(get_db)):
    """
    Generates a printable HTML report summary of campus biodiversity.
    """
    observations = db.query(Observation).order_by(Observation.observation_date.desc()).all()
    
    total_obs = len(observations)
    unique_sp = db.query(func.count(func.distinct(Observation.scientific_name))).filter(Observation.scientific_name.isnot(None)).scalar() or 0
    plants = db.query(func.count(Observation.id)).filter(Observation.category == "plant").scalar() or 0
    birds = db.query(func.count(Observation.id)).filter(Observation.category == "bird").scalar() or 0
    insects = db.query(func.count(Observation.id)).filter(Observation.category == "insect").scalar() or 0

    metrics = {
        "total_observations": total_obs,
        "unique_species": unique_sp,
        "plants_count": plants,
        "birds_count": birds,
        "insects_count": insects
    }

    html_content = generate_observations_html_report(observations, metrics)
    return HTMLResponse(content=html_content)
