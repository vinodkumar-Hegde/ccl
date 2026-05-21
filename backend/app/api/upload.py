from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from uuid import uuid4
import shutil

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)

BASE_UPLOAD_DIR = Path("storage")

ALLOWED_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "video/mp4"
}

BASE_UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/case")
async def upload_case_file(
    file: UploadFile = File(...)
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, PNG, JPG, JPEG and MP4 files are allowed"
        )

    file_extension = Path(file.filename).suffix

    safe_filename = f"{uuid4()}{file_extension}"

    save_path = BASE_UPLOAD_DIR / safe_filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    return {
        "original_filename": file.filename,
        "stored_filename": safe_filename,
        "content_type": file.content_type,
        "saved_to": str(save_path),
        "status": "uploaded"
    }