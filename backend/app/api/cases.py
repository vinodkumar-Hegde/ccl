from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.case_model import Case
from app.schemas.case_schema import CaseCreate, CaseResponse

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.post("/", response_model=CaseResponse)
def create_case(case: CaseCreate, db: Session = Depends(get_db)):
    new_case = Case(
        subject=case.subject,
        speciality=case.speciality,
        disease=case.disease,
        case_title=case.case_title,
        status="draft"
    )

    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    return new_case


@router.get("/", response_model=list[CaseResponse])
def list_cases(db: Session = Depends(get_db)):
    return db.query(Case).order_by(Case.id.desc()).all()


@router.get("/published", response_model=list[CaseResponse])
def list_published_cases(db: Session = Depends(get_db)):
    return (
        db.query(Case)
        .filter(Case.status == "published")
        .order_by(Case.id.desc())
        .all()
    )


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return case


@router.patch("/{case_id}/files")
def update_case_files(
    case_id: int,
    image_filename: str | None = None,
    lab_report_filename: str | None = None,
    video_filename: str | None = None,
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if image_filename:
        case.image_filename = image_filename

    if lab_report_filename:
        case.lab_report_filename = lab_report_filename

    if video_filename:
        case.video_filename = video_filename

    db.commit()
    db.refresh(case)

    return {
        "status": "success",
        "case_id": case.id,
        "image_filename": case.image_filename,
        "lab_report_filename": case.lab_report_filename,
        "video_filename": case.video_filename
    }


@router.patch("/{case_id}/status")
def update_case_status(
    case_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if status not in ["draft", "published"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    case.status = status

    db.commit()
    db.refresh(case)

    return {
        "status": "success",
        "case_id": case.id,
        "publish_status": case.status
    }


@router.delete("/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    db.delete(case)
    db.commit()

    return {
        "status": "deleted",
        "case_id": case_id
    }