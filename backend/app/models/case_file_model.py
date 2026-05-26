from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from datetime import datetime

from app.db.database import Base


class CaseFile(Base):
    __tablename__ = "case_files"

    id = Column(Integer, primary_key=True, index=True)

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=False
    )

    file_type = Column(String(50), nullable=False)
    filename = Column(String(300), nullable=False)
    original_name = Column(String(300), nullable=True)

    ai_analysis = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
      