from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class SpeciesResponse(BaseModel):
    id: Optional[int] = None
    scientific_name: str
    common_name: Optional[str] = None
    category: str = "other"
    taxonomic_rank: Optional[str] = "Species"
    kingdom: Optional[str] = None
    phylum: Optional[str] = None
    class_name: Optional[str] = None
    order: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    description: Optional[str] = None
    habitat: Optional[str] = None
    diet: Optional[str] = None
    behavior: Optional[str] = None
    reproduction: Optional[str] = None
    conservation: Optional[str] = None
    reference_images: List[Dict[str, Any]] = []
    observation_count: int = 0
    last_observed: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
