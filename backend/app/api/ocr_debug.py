from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.case_model import Case

router = APIRouter(
    prefix="/ocr-debug",
    tags=["OCR Debug"]
)


@router.get("/{case_id}")
def debug_case_ocr(
    case_id: int,
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return {
        "case_id": case.id,
        "title": case.case_title,
        "text_length": len(case.extracted_text or ""),
        "extracted_text": case.extracted_text or ""
    }
