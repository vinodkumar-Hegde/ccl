from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.case_model import Case

from app.services.ocr_service import (
    extract_text_from_pdf,
    extract_text_from_image
)

from app.services.llm_service import (
    generate_medical_summary
)

router = APIRouter(
    prefix="/process",
    tags=["AI Processing"]
)

@router.post("/case/{case_id}")
def process_case(
    case_id: int,
    filename: str,
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    file_path = Path("storage") / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        extracted_text = extract_text_from_pdf(str(file_path))
    elif suffix in [".png", ".jpg", ".jpeg"]:
        extracted_text = extract_text_from_image(str(file_path))
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type"
        )

    summary = generate_medical_summary(extracted_text)

    case.extracted_text = extracted_text
    case.ai_summary = summary
    case.status = "draft"

    db.commit()
    db.refresh(case)

    return {
        "status": "success",
        "case_id": case.id,
        "case_title": case.case_title,
        "extracted_text": case.extracted_text,
        "ai_summary": case.ai_summary,
        "publish_status": case.status
    }