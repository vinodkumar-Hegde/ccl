from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.case_model import Case
from app.services.flowchart_generator_service import generate_flowchart_from_summary

router = APIRouter(
    prefix="/flowchart",
    tags=["Flowchart AI"]
)


@router.post("/{case_id}")
def generate_case_flowchart(
    case_id: int,
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    ai_summary = case.ai_summary or {}

    flowchart = generate_flowchart_from_summary(ai_summary)

    ai_summary["flowchart"] = flowchart

    case.ai_summary = ai_summary

    db.commit()
    db.refresh(case)

    return {
        "case_id": case.id,
        "flowchart": flowchart,
        "ai_summary": case.ai_summary
    }
