from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DashboardMetrics(BaseModel):
    total_observations: int
    unique_species: int
    plants_count: int
    birds_count: int
    insects_count: int
    unknown_count: int
    confirmed_count: int
    pending_count: int

class SpeciesFrequency(BaseModel):
    scientific_name: str
    common_name: Optional[str] = None
    category: str
    count: int

class ZoneActivity(BaseModel):
    zone: str
    count: int

class TrendPoint(BaseModel):
    date: str
    plants: int = 0
    birds: int = 0
    insects: int = 0
    total: int = 0
