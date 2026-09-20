from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class IdentificationResult(Base):
    __tablename__ = "identification_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    observation_id = Column(String, ForeignKey("observations.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)
    model_name = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    category = Column(String, nullable=False)
    rank = Column(Integer, nullable=False)
    scientific_name = Column(String, nullable=False)
    common_name = Column(String, nullable=True)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    observation = relationship("Observation", back_populates="identification_results")
