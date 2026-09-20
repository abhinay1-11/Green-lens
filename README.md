# GreenLens — AI Biodiversity Monitor

**GreenLens** is a state-of-the-art AI-powered biodiversity monitoring web application designed for ecological survey, wildlife identification, and biodiversity analytics. It provides real-time species classification across avian, plant, and insect domains, enriched with global biodiversity taxonomy, quick facts, field notes, and digital collection book management.

---

## 🌟 Key Features

* **Multi-Domain AI Classification**:
  - 🦅 **Bird Identification**: Powered by **BioCLIP 2 (`imageomics/bioclip-2`)** tree-of-life classifier across 10,000+ avian species.
  - 🌿 **Plant Identification**: Powered by **Pl@ntNet API v2** with fallback biodiversity vision engines.
  - 🐝 **Insect Identification**: Powered by **Insecta Vision AI** engine.
* **Global Species Explorer**:
  - Real-time global species search querying **GBIF (Global Biodiversity Information Facility)** and **Wikipedia REST APIs**.
  - Categorized taxonomy filters (*All, Birds, Plants, Trees, Insects, Other*).
  - Client-side query caching, 300ms input debouncing, and `AbortController` stale request cancellation.
* **Automated Species Enrichment**:
  - Live taxonomy breakdown (Kingdom, Phylum, Class, Order, Family, Genus, Species).
  - Quick Facts extraction (Habitat, Diet, Behavior, Reproduction, Conservation Status).
  - Verified reference photograph galleries from GBIF & Wikimedia.
* **Observation Recording & Geo-location**:
  - Browser Geolocation API integration (`Use Live Location`).
  - Manual location input fallback (`Enter Location Manually`).
  - Field notes & habitat observation log persistence.
* **Digital Species Collections**:
  - Custom digital field collection books ("My Bird Collection", "Campus Plants").
  - One-click PDF field report generation using ReportLab.
  - CSV observation export for ecological research.
* **Analytics & Reports**:
  - Diversity distribution charts, temporal observation trends, and species breakdown.
* **Refined Taste UI/UX**:
  - Glassmorphism dark mode design system.
  - Fully mobile-responsive layout with zero horizontal overflow.
  - Theme system with **Dark**, **Light**, and **System** mode persistence.

---

## 🏗 Architecture & Tech Stack

```text
  ┌─────────────────────────────────────────────────────────┐
  │                 Vite + React Frontend                   │
  │     (Tailwind/Glassmorphism CSS, Lucide Icons, Axios)   │
  └────────────────────────────┬────────────────────────────┘
                               │ HTTP / REST API
  ┌────────────────────────────▼────────────────────────────┐
  │                   FastAPI Backend                       │
  │       (App Lifespan Singleton, Uvicorn, SQLite DB)      │
  └───────┬────────────────────┬────────────────────┬───────┘
          │                    │                    │
  ┌───────▼──────┐    ┌────────▼───────┐    ┌───────▼──────┐
  │  BioCLIP 2   │    │  Pl@ntNet API  │    │ GBIF & Wiki  │
  │ Bird Engine  │    │  Plant Engine  │    │ REST Services│
  └──────────────┘    └────────────────┘    └──────────────┘
```

* **Frontend**: React 18, Vite 5, Axios, Lucide React icons, Vanilla CSS Design System.
* **Backend**: Python 3.11+, FastAPI, SQLAlchemy, PyDantic v2, ReportLab, Pillow, HTTPX.
* **AI Models**: BioCLIP 2 (`imageomics/bioclip-2`), Pl@ntNet API v2, Insecta Vision AI.

---

## 📁 Project Structure

```text
greenlens/
├── backend/
│   ├── app/
│   │   ├── config.py                  # Environment configuration settings
│   │   ├── database.py                # SQLite database setup & schema migrations
│   │   ├── main.py                    # FastAPI app entry point & lifespan pre-warming
│   │   ├── models/                    # SQLAlchemy database models
│   │   ├── routers/                   # API routes (health, identification, species, collections, etc.)
│   │   ├── schemas/                   # PyDantic request/response validation schemas
│   │   ├── services/                  # Identification providers & species enrichment
│   │   └── utils/                     # Confidence normalization & image validation
│   ├── tests/                         # Pytest automated test suite
│   ├── Dockerfile                     # Production container configuration
│   └── requirements.txt               # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/                # Reusable UI components (collections, badges, layout)
│   │   ├── pages/                     # Application views (Dashboard, Observe, SpeciesExplorer, etc.)
│   │   ├── services/api.js            # Axios API service client
│   │   └── utils/theme.js             # Theme switcher state manager
│   ├── package.json                   # Frontend npm dependencies
│   ├── vercel.json                    # Vercel deployment configuration
│   └── vite.config.js                 # Vite build configuration
├── data/                              # Test images & dataset files
├── .env.example                       # Root environment variables blueprint
├── .gitignore                         # Production git ignore configuration
├── render.yaml                        # Render cloud deployment blueprint
└── README.md                          # Project documentation
```

---

## 🚀 Local Development Setup

### Prerequisites
* **Node.js**: v18+
* **Python**: 3.10+

### 1. Backend Setup
```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Start FastAPI development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend API will run at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The frontend application will run at `http://localhost:5173`.

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` in both `backend/` and `frontend/`:

### Backend (`backend/.env`)
| Variable | Default | Description |
| :--- | :--- | :--- |
| `IDENTIFICATION_MODE` | `real` | Set to `real` for live AI engines or `mock` for testing |
| `PLANTNET_API_KEY` | *(Optional)* | Pl@ntNet API Key for live plant classification |
| `BIRD_IDENTIFICATION_PROVIDER` | `bioclip` | Active bird provider adapter |
| `BIRD_MIN_CONFIDENCE` | `0.30` | Minimum confidence threshold for HIGH/MEDIUM status |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated URLs in production) |
| `PORT` | `8000` | Port for backend service binding |

### Frontend (`frontend/.env`)
| Variable | Default | Description |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `/api` | Production backend API URL (e.g. `https://api.greenlens.app/api`) |

---

## ☁️ Production Architecture & Deployment

GreenLens uses a decoupled production architecture:
- **Frontend**: React SPA deployed on **Vercel** (`https://green-lens-five.vercel.app/`).
- **Backend**: FastAPI AI identification service deployed on a Python-compatible cloud platform (**Render** or **Railway**).

### Backend Deployment (Render / Railway)
1. **Repository Link**: Connect `https://github.com/abhinay1-11/Green-lens.git` to Render or Railway.
2. **Build Command**: `pip install -r backend/requirements.txt` (or `pip install -r requirements.txt` if Root Directory is set to `backend`).
3. **Start Command**:
   - If Root Directory is repo root: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - If Root Directory is `backend`: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables**:
   - `IDENTIFICATION_MODE=real`
   - `CORS_ORIGINS=https://green-lens-five.vercel.app`
   - `PLANTNET_API_KEY` *(Optional key for Pl@ntNet API)*

### Frontend Deployment (Vercel)
1. Connect `https://github.com/abhinay1-11/Green-lens.git` to Vercel.
2. Set Environment Variable in Vercel Project Settings:
   - `VITE_API_BASE_URL` = `<PUBLIC_FASTAPI_BACKEND_URL>` (e.g. `https://greenlens-backend.onrender.com`)
3. Trigger a fresh Vercel build so Vite bakes `VITE_API_BASE_URL` into the production JavaScript bundle.


---

## 🧪 Testing & Verification

### Automated Backend Test Suite
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Production Build Test
```bash
cd frontend
npm run build
```

---

## 📜 Data Sources & Attribution

- **Avian AI Classification**: BioCLIP 2 (*TreeOfLifeClassifier*) by Imageomics.
- **Global Biodiversity Data**: [GBIF REST API](https://www.gbif.org/) (Global Biodiversity Information Facility).
- **Species Summaries**: [Wikipedia REST API](https://en.wikipedia.org/api/rest_v1/).
- **Plant Classification**: [Pl@ntNet API](https://my.plantnet.org/).

---

## ⚖️ Known Infrastructure Limitations

* **Model Memory Footprint**: BioCLIP 2 loads ~4.5 GB tree-of-life embeddings into memory during application startup. Ensure production backend hosting instances provide at least 4 GB RAM.
* **SQLite Single-File Storage**: SQLite is used for persistent local storage and enrichment caching. For multi-node cloud deployments, configure PostgreSQL via `DATABASE_URL`.
