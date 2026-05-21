from pydantic import BaseModel
from typing import Optional, Any


class CaseCreate(BaseModel):
    subject: str
    speciality: str
    disease: str
    case_title: str


class CaseResponse(BaseModel):
    id: int
    subject: str
    speciality: str
    disease: str
    case_title: str

    status: str
    processing_status: Optional[str] = None

    extracted_text: Optional[str] = None
    ai_summary: Optional[Any] = None

    class Config:
        from_attributes = True
