from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from app.db.database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)

    case_title = Column(String, nullable=False)

    subject = Column(String, nullable=True)
    speciality = Column(String, nullable=True)
    super_speciality = Column(String, nullable=True)
    disease = Column(String, nullable=True)

    processing_status = Column(String, default="pending")
    status = Column(String, default="draft")

    extracted_text = Column(Text, nullable=True)
    ai_summary = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
