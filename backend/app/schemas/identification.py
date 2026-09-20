from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

class PredictionItem(BaseModel):
    rank: int
    scientific_name: str
    common_names: List[str] = []
    confidence: float = Field(..., ge=0.0, le=1.0)
    taxonomic_rank: Optional[str] = "species"

    model_config = ConfigDict(from_attributes=True)

class ErrorDetail(BaseModel):
    code: str
    message: str

class PredictionResponse(BaseModel):
    success: bool = True
    category: str
    detected_category: Optional[str] = None
    provider: str
    model_name: Optional[str] = None
    model_version: Optional[str] = "1.0.0"
    identification_status: str = "HIGH_CONFIDENCE"  # HIGH_CONFIDENCE, MEDIUM_CONFIDENCE, LOW_CONFIDENCE, UNIDENTIFIED, IDENTIFICATION_UNAVAILABLE
    predictions: List[PredictionItem] = []
    species_profile: Optional[Dict[str, Any]] = None
    is_mock: bool = False
    error: Optional[ErrorDetail] = None

    model_config = ConfigDict(from_attributes=True)

