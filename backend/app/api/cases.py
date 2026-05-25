import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.case_model import Case


router = APIRouter(
    prefix="/cases",
    tags=["Cases"]
)


def normalize_ai_summary(value):
    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {}

    return {}


def serialize_case(case: Case):
    return {
        "id": case.id,
        "case_title": case.case_title,
        "subject": case.subject,
        "speciality": case.speciality,
        "super_speciality": case.super_speciality,
        "disease": case.disease,
        "status": case.status,
        "processing_status": case.processing_status,
        "extracted_text": case.extracted_text,
        "ai_summary": normalize_ai_summary(case.ai_summary),
        "created_at": str(case.created_at) if getattr(case, "created_at", None) else None,
    }


@router.get("/")
def list_cases(db: Session = Depends(get_db)):
    cases = db.query(Case).order_by(Case.id.desc()).all()
    return [serialize_case(case) for case in cases]


@router.get("/published")
def list_published_cases(db: Session = Depends(get_db)):
    cases = (
        db.query(Case)
        .filter(Case.status == "published")
        .order_by(Case.id.desc())
        .all()
    )

    return [serialize_case(case) for case in cases]


@router.get("/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return serialize_case(case)
