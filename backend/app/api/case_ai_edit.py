from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.case_model import Case

router = APIRouter(
    prefix="/case-ai",
    tags=["Case AI Edit"]
)


@router.put("/{case_id}")
def update_case_ai(
    case_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(
        Case.id == case_id
    ).first()

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    case.ai_summary = payload

    db.commit()

    db.refresh(case)

    return {
        "status": "updated",
        "ai_summary": case.ai_summary
    }