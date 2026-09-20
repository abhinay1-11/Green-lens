import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.config import settings

DB_PATH = getattr(settings, "DATABASE_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "greenlens.db"))
TTL_DAYS = 7

def get_db_connection():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_cache_db():
    try:
        with get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS species_enrichment_cache (
                    scientific_name TEXT PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
    except Exception as exc:
        print(f"[SpeciesCache] Failed to initialize DB table: {exc}")

init_cache_db()

def get_cached_species_profile(scientific_name: str) -> Optional[Dict[str, Any]]:
    if not scientific_name:
        return None
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT profile_json, updated_at FROM species_enrichment_cache WHERE scientific_name = ?",
                (scientific_name.strip().lower(),)
            )
            row = cursor.fetchone()
            if row:
                profile_data = json.loads(row["profile_json"])
                # Check TTL
                updated_at_str = row["updated_at"]
                if updated_at_str:
                    try:
                        updated_at = datetime.fromisoformat(updated_at_str)
                        if datetime.utcnow() - updated_at > timedelta(days=TTL_DAYS):
                            return None  # Expired
                    except Exception:
                        pass
                return profile_data
    except Exception as exc:
        print(f"[SpeciesCache] Error reading cache for '{scientific_name}': {exc}")
    return None

def set_cached_species_profile(scientific_name: str, profile_data: Dict[str, Any]) -> None:
    if not scientific_name or not profile_data:
        return
    try:
        now = datetime.utcnow().isoformat()
        profile_json = json.dumps(profile_data)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO species_enrichment_cache (scientific_name, profile_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(scientific_name) DO UPDATE SET
                    profile_json = excluded.profile_json,
                    updated_at = excluded.updated_at;
            """, (scientific_name.strip().lower(), profile_json, now, now))
            conn.commit()
    except Exception as exc:
        print(f"[SpeciesCache] Error writing cache for '{scientific_name}': {exc}")
