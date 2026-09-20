# GreenLens API Documentation

## Base URL
`/api`

## Endpoints

### Health & Status
- `GET /api/health` — Returns system health and current engine mode.
- `GET /api/providers/status` — Returns status of identification service adapters.

### Species Identification
- `POST /api/identification/predict` — Multipart upload (1-5 images) with category and organ parameters. Returns normalized predictions.

### Observations
- `GET /api/observations` — Query list of observations (filters: category, zone, verification, search).
- `POST /api/observations` — Create new observation.
- `GET /api/observations/{id}` — Get detailed observation and AI history.
- `PATCH /api/observations/{id}` — Update verification or location.
- `DELETE /api/observations/{id}` — Delete observation.

### Species Explorer & Taxonomy
- `GET /api/species/search` — Search campus species database & GBIF taxonomy.
- `GET /api/species/{id}` — Species profile with observations and taxonomy hierarchy.

### Analytics & Reports
- `GET /api/analytics/dashboard` — Live DB metrics summary.
- `GET /api/analytics/trends` — Time-series and zone breakdown.
- `GET /api/analytics/map` — GeoJSON observation feature collection for map.
- `GET /api/reports/observations.csv` — Download CSV dump.
- `GET /api/reports/observations.pdf` — Download printable HTML/PDF report.
