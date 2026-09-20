from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class Observation(Base):
    __tablename__ = "observations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)
    category = Column(String, index=True, nullable=False) # plant, bird, insect, unknown
    scientific_name = Column(String, index=True, nullable=True)
    common_name = Column(String, index=True, nullable=True)
    taxon_id = Column(String, nullable=True)
    
    # Dates
    observation_date = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Location
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    location_accuracy = Column(Float, nullable=True)
    campus_zone = Column(String, index=True, nullable=True)
    notes = Column(Text, nullable=True)
    
    # AI Identification details
    ai_provider = Column(String, nullable=True)
    ai_model_version = Column(String, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_predicted_scientific_name = Column(String, nullable=True)
    ai_predicted_common_name = Column(String, nullable=True)
    
    # Human Verification details
    # Options: pending, ai_suggested, user_confirmed, user_corrected, expert_verified, rejected, unidentified
    verification_status = Column(String, default="ai_suggested", index=True)
    
    # Relationships
    images = relationship("ObservationImage", back_populates="observation", cascade="all, delete-orphan")
    identification_results = relationship("IdentificationResult", back_populates="observation", cascade="all, delete-orphan")
