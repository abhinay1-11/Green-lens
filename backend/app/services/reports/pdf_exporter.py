from typing import List, Dict, Any
from app.models.observation import Observation
from datetime import datetime

def generate_observations_html_report(observations: List[Observation], metrics: Dict[str, Any]) -> str:
    """
    Generates a printable HTML report document for biodiversity observations.
    """
    now_str = datetime.utcnow().strftime("%B %d, %Y")

    rows_html = ""
    for obs in observations:
        conf_str = f"{round(obs.ai_confidence * 100)}%" if obs.ai_confidence is not None else "N/A"
        date_str = obs.observation_date.strftime("%Y-%m-%d") if obs.observation_date else ""
        rows_html += f"""
        <tr>
            <td><code>{obs.id[:8]}</code></td>
            <td>{date_str}</td>
            <td><span class="badge badge-{obs.category}">{obs.category.capitalize()}</span></td>
            <td><strong>{obs.common_name or '—'}</strong><br/><small style="color:#666;">{obs.scientific_name or ''}</small></td>
            <td>{conf_str}</td>
            <td>{obs.ai_provider or '—'}</td>
            <td>{obs.verification_status}</td>
            <td>{obs.campus_zone or '—'}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>GreenLens Campus Biodiversity Report</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #111; padding: 40px; max-width: 900px; margin: 0 auto; line-height: 1.6; }}
        .header {{ border-bottom: 3px solid #10b981; padding-bottom: 15px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: flex-end; }}
        .title {{ font-size: 28px; font-weight: bold; color: #064e3b; margin: 0; }}
        .subtitle {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
        .metric-card {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 15px; text-align: center; }}
        .metric-num {{ font-size: 24px; font-weight: bold; color: #047857; }}
        .metric-label {{ font-size: 12px; text-transform: uppercase; color: #065f46; letter-spacing: 0.05em; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px; }}
        th {{ background: #f3f4f6; text-align: left; padding: 10px; border-bottom: 2px solid #e5e7eb; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; color: #4b5563; }}
        td {{ padding: 10px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }}
        .badge {{ padding: 3px 8px; border-radius: 12px; font-size: 10px; font-weight: bold; text-transform: uppercase; }}
        .badge-plant {{ background: #d1fae5; color: #047857; }}
        .badge-bird {{ background: #dbeafe; color: #1d4ed8; }}
        .badge-insect {{ background: #fef3c7; color: #b45309; }}
        .footer {{ margin-top: 40px; border-top: 1px solid #e5e7eb; padding-top: 15px; font-size: 11px; color: #9ca3af; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1 class="title">GreenLens Biodiversity Report</h1>
            <div class="subtitle">AI-Powered Campus Environmental Audit</div>
        </div>
        <div style="text-align: right; font-size: 12px; color: #666;">
            Generated on: {now_str}<br/>
            Campus: Central Campus
        </div>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-num">{metrics.get('total_observations', 0)}</div>
            <div class="metric-label">Total Observations</div>
        </div>
        <div class="metric-card">
            <div class="metric-num">{metrics.get('unique_species', 0)}</div>
            <div class="metric-label">Unique Species</div>
        </div>
        <div class="metric-card">
            <div class="metric-num">{metrics.get('plants_count', 0)}</div>
            <div class="metric-label">Plants Recorded</div>
        </div>
        <div class="metric-card">
            <div class="metric-num">{metrics.get('birds_count', 0)} / {metrics.get('insects_count', 0)}</div>
            <div class="metric-label">Birds / Insects</div>
        </div>
    </div>

    <h2>Observation Records</h2>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Date</th>
                <th>Category</th>
                <th>Species Name</th>
                <th>AI Conf</th>
                <th>Engine</th>
                <th>Verification</th>
                <th>Zone</th>
            </tr>
        </thead>
        <tbody>
            {rows_html if rows_html else '<tr><td colspan="8" style="text-align:center;">No observations recorded.</td></tr>'}
        </tbody>
    </table>

    <div class="footer">
        GreenLens Biodiversity Platform — Separating AI prediction probabilities from human-verified ecological records.
    </div>
</body>
</html>"""
    return html
