from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.case_model import Case

from app.services.rag_service import (
    index_case_text,
    search_cases,
    answer_with_rag
)

router = APIRouter(
    prefix="/rag",
    tags=["RAG"]
)


@router.post("/index/{case_id}")
def index_case(
    case_id: int,
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

    if not case.extracted_text:
        raise HTTPException(
            status_code=400,
            detail="No extracted text found"
        )

    return index_case_text(
        case_id=case.id,
        case_title=case.case_title,
        text=case.extracted_text
    )


@router.get("/search")
def search_clinical_cases(
    query: str,
    limit: int = 5
):
    return {
        "query": query,
        "results": search_cases(query, limit)
    }


@router.get("/ask")
def ask_clinical_ai(
    query: str,
    limit: int = 5
):
    return answer_with_rag(query, limit)