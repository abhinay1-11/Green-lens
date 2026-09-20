import csv
import io
from typing import List
from app.models.observation import Observation

def generate_observations_csv(observations: List[Observation]) -> str:
    """
    Generates CSV string export for a list of Observation database records.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers matching PRD section 48
    writer.writerow([
        "Observation ID",
        "Date",
        "Category",
        "Common Name",
        "Scientific Name",
        "AI Confidence",
        "Provider",
        "Verification Status",
        "Latitude",
        "Longitude",
        "Campus Zone",
        "Notes"
    ])

    for obs in observations:
        conf_str = f"{round(obs.ai_confidence * 100)}%" if obs.ai_confidence is not None else "N/A"
        date_str = obs.observation_date.strftime("%Y-%m-%d %H:%M:%S") if obs.observation_date else ""
        
        writer.writerow([
            obs.id,
            date_str,
            obs.category.capitalize() if obs.category else "Unknown",
            obs.common_name or "",
            obs.scientific_name or "",
            conf_str,
            obs.ai_provider or "N/A",
            obs.verification_status or "pending",
            obs.latitude if obs.latitude is not None else "",
            obs.longitude if obs.longitude is not None else "",
            obs.campus_zone or "",
            obs.notes or ""
        ])

    return output.getvalue()
