from fastapi import APIRouter
from pydantic import BaseModel

from app.services.llm_service import generate_medical_summary

router = APIRouter(
    prefix="/ai",
    tags=["AI Summary"]
)

class SummaryRequest(BaseModel):
    text: str

@router.post("/summary")
def create_summary(request: SummaryRequest):
    summary = generate_medical_summary(request.text)

    return {
        "status": "success",
        "summary": summary
    }