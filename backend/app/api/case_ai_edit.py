from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.db.database import get_db
from app.models.case_model import Case


router = APIRouter(
    prefix="/case-ai",
    tags=["Case AI Edit"]
)


class CaseAIUpdateRequest(BaseModel):
    ai_summary: Dict[str, Any]
    status: Optional[str] = None


def normalize_ai_summary(value):
    if isinstance(value, dict):
        return value

    return {}


@router.put("/{case_id}")
def update_case_ai(
    case_id: int,
    payload: CaseAIUpdateRequest,
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        existing_summary = normalize_ai_summary(case.ai_summary)

        updated_summary = {
            **existing_summary,
            **payload.ai_summary
        }

        case.ai_summary = updated_summary
        flag_modified(case, "ai_summary")

        # Important: edited case should not remain "processing"
        case.processing_status = "completed"

        if payload.status:
            case.status = payload.status

        db.commit()
        db.refresh(case)

        return {
            "message": "Case AI summary updated successfully",
            "case_id": case.id,
            "status": case.status,
            "processing_status": case.processing_status,
            "ai_summary": case.ai_summary
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update case AI summary: {str(error)}"
        )


@router.patch("/{case_id}/status")
def update_case_status(
    case_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        case.status = status

        if status == "published":
            case.processing_status = "completed"

        db.commit()
        db.refresh(case)

        return {
            "message": "Case status updated successfully",
            "case_id": case.id,
            "status": case.status,
            "processing_status": case.processing_status
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update status: {str(error)}"
        )
