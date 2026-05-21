from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pathlib import Path
from uuid import uuid4
import shutil

from app.db.database import get_db
from app.models.case_model import Case
from app.models.case_file_model import CaseFile
from app.services.case_processing_service import process_case_background

router = APIRouter(prefix="/full-process", tags=["Full Case Processing"])

STORAGE_DIR = Path("storage")
STORAGE_DIR.mkdir(exist_ok=True)


def save_file(file: UploadFile | None):
    if file is None:
        return None

    ext = Path(file.filename).suffix
    filename = f"{uuid4()}{ext}"
    file_path = STORAGE_DIR / filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return filename


def save_case_file(db, case_id, file, file_type):
    stored_filename = save_file(file)

    if not stored_filename:
        return None

    record = CaseFile(
        case_id=case_id,
        file_type=file_type,
        filename=stored_filename,
        original_name=file.filename,
        ai_analysis=None
    )

    db.add(record)
    return record


@router.post("/case")
async def full_process_case(
    background_tasks: BackgroundTasks,
    subject: str = Form(...),
    speciality: str = Form(...),
    disease: str = Form(...),
    case_title: str = Form(...),
    case_sheet: UploadFile = File(...),
    lab_reports: list[UploadFile] | None = File(None),
    images: list[UploadFile] | None = File(None),
    videos: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db)
):
    new_case = Case(
        subject=subject,
        speciality=speciality,
        disease=disease,
        case_title=case_title,
        status="draft",
        processing_status="queued"
    )

    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    save_case_file(db, new_case.id, case_sheet, "case_sheet")

    if lab_reports:
        for file in lab_reports:
            save_case_file(db, new_case.id, file, "lab_report")

    if images:
        for file in images:
            save_case_file(db, new_case.id, file, "image")

    if videos:
        for file in videos:
            save_case_file(db, new_case.id, file, "video")

    db.commit()

    background_tasks.add_task(
        process_case_background,
        new_case.id
    )

    return {
        "status": "success",
        "case_id": new_case.id,
        "publish_status": new_case.status,
        "processing_status": new_case.processing_status,
        "message": "Case uploaded. AI processing started in background."
    }
