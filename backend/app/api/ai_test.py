from fastapi import APIRouter
from pydantic import BaseModel

from app.services.llm_service import generate_medical_summary

router = APIRouter(prefix="/ai-test", tags=["AI Test"])


class TestPayload(BaseModel):
    text: str


@router.post("/summary")
def test_summary(payload: TestPayload):
    result = generate_medical_summary(payload.text)

    return {
        "input_length": len(payload.text),
        "summary": result
    }
