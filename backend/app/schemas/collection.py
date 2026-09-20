from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class CollectionItemCreate(BaseModel):
    item_type: str = "observation"  # "observation" or "explored"
    scientific_name: str
    common_name: Optional[str] = None
    category: Optional[str] = "other"
    observation_id: Optional[str] = None


class CollectionItemResponse(BaseModel):
    id: int
    collection_id: int
    item_type: str
    scientific_name: str
    common_name: Optional[str] = None
    category: Optional[str] = "other"
    observation_id: Optional[str] = None
    created_at: datetime

    # Augmented fields
    observation_image_url: Optional[str] = None
    reference_image_url: Optional[str] = None
    confidence: Optional[float] = None
    observation_date: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CollectionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    species_count: int = 0
    observation_count: int = 0
    cover_image_url: Optional[str] = None
    items: List[CollectionItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
