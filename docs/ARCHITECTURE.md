# GreenLens System Architecture

## System Diagram

```text
PHOTO UPLOAD / CAPTURE
  │
  ▼
IMAGE VALIDATION (MIME, Magic bytes, Max 10MB, Dimensions)
  │
  ▼
CATEGORY (Plant / Bird / Insect / Unknown)
  │
  ▼
IDENTIFICATION PROVIDER INTERFACE
  ├── PlantNetProvider (Pl@ntNet REST v2)
  ├── BirdProvider (Pretrained / Open API)
  ├── InsectProvider (Pretrained / Open API)
  └── MockProvider (Development & Demo mode)
  │
  ▼
AI PREDICTIONS (Normalized 0–1 score to percentage, rank, species names)
  │
  ▼
HUMAN REVIEW (Confirm / Correct / Reject / Manual Search)
  │
  ▼
LOCATION VALIDATION (GPS / Map picker / Campus Zone / GeoJSON Boundary Check)
  │
  ▼
SQLITE / POSTGRES DATABASE
  ├── observations
  ├── observation_images
  ├── identification_results
  └── species
  │
  ▼
APPLICATION SERVICES
  ├── Interactive Leaflet Map
  ├── Analytics Dashboard
  ├── Species Explorer (GBIF Integration)
  └── Reports (CSV / PDF Exporter)
```

## Provider Abstraction Policy
- Never couple external APIs directly to React components.
- Implement all providers behind `IdentificationProvider`.
- Fall back to `MockProvider` when credentials or network services are unavailable.
- Display `DEMO / MOCK RESULT` badge clearly when mock predictions are returned.
