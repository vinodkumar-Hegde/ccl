from fastapi import APIRouter, HTTPException
from pathlib import Path

from app.services.ocr_service import (
    extract_text_from_pdf,
    extract_text_from_image
)

router = APIRouter(
    prefix="/ocr",
    tags=["OCR"]
)

@router.post("/extract")
def extract_text(filename: str):
    try:
        file_path = Path("storage") / filename

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )

        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            text = extract_text_from_pdf(str(file_path))
        elif suffix in [".png", ".jpg", ".jpeg"]:
            text = extract_text_from_image(str(file_path))
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type"
            )

        return {
            "status": "success",
            "filename": filename,
            "extracted_text": text
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
