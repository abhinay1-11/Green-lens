from sqlalchemy import Column, String, Integer, Text, DateTime
from datetime import datetime
from app.database import Base

class Species(Base):
    __tablename__ = "species"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scientific_name = Column(String, unique=True, index=True, nullable=False)
    common_name = Column(String, index=True, nullable=True)
    category = Column(String, index=True, nullable=False) # plant, bird, insect
    kingdom = Column(String, nullable=True)
    phylum = Column(String, nullable=True)
    class_name = Column("class", String, nullable=True)
    order = Column(String, nullable=True)
    family = Column(String, nullable=True)
    genus = Column(String, nullable=True)
    species = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    habitat = Column(Text, nullable=True)
    source = Column(String, default="GBIF / GreenLens")
    source_url = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
