from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class ObservationImage(Base):
    __tablename__ = "observation_images"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    observation_id = Column(String, ForeignKey("observations.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    organ = Column(String, default="auto")
    checksum = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    observation = relationship("Observation", back_populates="images")
