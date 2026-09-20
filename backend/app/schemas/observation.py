from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class ImageBase(BaseModel):
    file_path: str
    original_filename: str
    mime_type: str
    file_size: int
    organ: Optional[str] = "auto"
    width: Optional[int] = None
    height: Optional[int] = None

class ImageCreate(ImageBase):
    pass

class ImageResponse(ImageBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ObservationBase(BaseModel):
    category: str
    scientific_name: Optional[str] = None
    common_name: Optional[str] = None
    taxon_id: Optional[str] = None
    
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_accuracy: Optional[float] = None
    campus_zone: Optional[str] = None
    notes: Optional[str] = None
    
    ai_provider: Optional[str] = None
    ai_model_version: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_predicted_scientific_name: Optional[str] = None
    ai_predicted_common_name: Optional[str] = None
    
    verification_status: Optional[str] = "user_confirmed"

class ObservationCreate(ObservationBase):
    image_paths: List[str] = []
    organ_tags: List[str] = []
    predictions_history: Optional[List[dict]] = None

class ObservationUpdate(BaseModel):
    scientific_name: Optional[str] = None
    common_name: Optional[str] = None
    verification_status: Optional[str] = None
    campus_zone: Optional[str] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class IdentificationResultResponse(BaseModel):
    id: str
    provider: str
    rank: int
    scientific_name: str
    common_name: Optional[str] = None
    confidence: float

    model_config = ConfigDict(from_attributes=True)

class ObservationResponse(ObservationBase):
    id: str
    user_id: Optional[str] = None
    observation_date: datetime
    created_at: datetime
    images: List[ImageResponse] = []
    identification_results: List[IdentificationResultResponse] = []

    model_config = ConfigDict(from_attributes=True)
