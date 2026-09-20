from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

class ReferenceImage(BaseModel):
    url: str
    thumbnail_url: Optional[str] = None
    source: str = "GBIF / External"
    creator: Optional[str] = "Unknown Creator"
    license: Optional[str] = None
    license_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SpeciesFacts(BaseModel):
    habitat: Optional[str] = None
    diet: Optional[str] = None
    behavior: Optional[str] = None
    reproduction: Optional[str] = None
    conservation: Optional[str] = None
    conservation_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SpeciesTaxonomy(BaseModel):
    kingdom: Optional[str] = None
    phylum: Optional[str] = None
    class_name: Optional[str] = Field(None, alias="class")
    order: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    species: Optional[str] = None
    rank: Optional[str] = "Species"

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class SpeciesProfile(BaseModel):
    available: bool = True
    scientific_name: str
    common_name: Optional[str] = None
    description: Optional[str] = None
    taxonomy: SpeciesTaxonomy = Field(default_factory=SpeciesTaxonomy)
    facts: SpeciesFacts = Field(default_factory=SpeciesFacts)
    reference_images: List[ReferenceImage] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
