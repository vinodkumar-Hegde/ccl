from pydantic import BaseModel
from typing import Optional, Any


class CaseFileResponse(BaseModel):
    id: int
    case_id: int
    file_type: str
    filename: str
    original_name: Optional[str] = None
    ai_analysis: Optional[Any] = None

    class Config:
        from_attributes = True