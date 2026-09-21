import os
import sys
from pathlib import Path

# Ensure 'backend' directory is in sys.path when running from repo root
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings

from app.database import Base, engine, migrate_collections_schema
from app.routers import health, providers, identification, observations, species, analytics, reports, collections

# Print safe startup diagnostics
def print_startup_diagnostics():
    has_key = bool(settings.clean_plantnet_api_key)
    print("\n==================================================")
    print("GreenLens Backend Identification Pipeline Diagnostics")
    print("==================================================")
    print(f"Identification Mode: {settings.IDENTIFICATION_MODE.upper()}")
    print(f"Plant Provider: Pl@ntNet API v2")
    print(f"PlantNet API Key Configured: {'YES' if has_key else 'NO'}")
    print(f"Bird Provider: {settings.BIRD_IDENTIFICATION_PROVIDER}")
    print(f"Insect Provider: {settings.INSECT_IDENTIFICATION_PROVIDER}")
    print("==================================================\n")

print_startup_diagnostics()

# Migrate legacy collection schemas safely if present
migrate_collections_schema(engine)

# Create DB tables
Base.metadata.create_all(bind=engine)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

from contextlib import asynccontextmanager
import threading
import time
from app.services.species_enrichment import SpeciesEnrichmentService
from app.services.species_enrichment.session import get_http_session

def _bg_warmup():
    try:
        session = get_http_session()
        session.get("https://api.gbif.org/v1/species/match?name=Apis%20mellifera", timeout=3.0)
        session.get("https://en.wikipedia.org/api/rest_v1/page/summary/Apis_mellifera", timeout=3.0)
        for sp in ["Centrocercus urophasianus", "Azadirachta indica", "Apis mellifera"]:
            SpeciesEnrichmentService.get_species_profile(sp)
    except Exception as e:
        print(f"[Warmup] Note: {e}")

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    print("\n[STARTUP] GreenLens AI services starting...")
    t_start = time.time()
    
    if settings.BIRD_IDENTIFICATION_PROVIDER == "bioclip" or settings.INSECT_IDENTIFICATION_PROVIDER == "bioclip":
        print("[STARTUP] BioCLIP: lazy initialization enabled")

    # Initialize reusable HTTP species session
    try:
        get_http_session()
        print("[STARTUP] Species services initialized")
    except Exception as e:
        print(f"[STARTUP] Species services note: {e}")

    # Background warm up for external biodiversity connectivity
    threading.Thread(target=_bg_warmup, daemon=True).start()
    print(f"[STARTUP] GreenLens AI services ready in {time.time() - t_start:.2f}s\n")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Biodiversity Monitoring API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for React Vite frontend
allowed_origins_env = os.getenv("CORS_ORIGINS", "*")
if allowed_origins_env == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(health.router)
app.include_router(providers.router)
app.include_router(identification.router)
app.include_router(observations.router)
app.include_router(species.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(collections.router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
