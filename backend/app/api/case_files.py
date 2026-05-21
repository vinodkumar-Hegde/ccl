from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.case_file_model import CaseFile
from app.schemas.case_file_schema import CaseFileResponse

router = APIRouter(
    prefix="/case-files",
    tags=["Case Files"]
)


@router.get("/{case_id}", response_model=list[CaseFileResponse])
def get_case_files(
    case_id: int,
    db: Session = Depends(get_db)
):
    files = (
        db.query(CaseFile)
        .filter(CaseFile.case_id == case_id)
        .order_by(CaseFile.id.asc())
        .all()
    )

    return files


@router.get("/{case_id}/{file_type}", response_model=list[CaseFileResponse])
def get_case_files_by_type(
    case_id: int,
    file_type: str,
    db: Session = Depends(get_db)
):
    allowed_types = [
        "case_sheet",
        "lab_report",
        "image",
        "video"
    ]

    if file_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type"
        )

    files = (
        db.query(CaseFile)
        .filter(
            CaseFile.case_id == case_id,
            CaseFile.file_type == file_type
        )
        .order_by(CaseFile.id.asc())
        .all()
    )

    return files