from pathlib import Path
import fitz
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

from app.db.database import SessionLocal
from app.models.case_model import Case
from app.models.case_file_model import CaseFile
from app.services.ollama_service import generate_structured_summary
from app.services.lab_report_service import analyze_lab_report_text
from app.services.case_reconstruction_service import reconstruct_teaching_case


STORAGE_DIR = Path("storage")


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    image = image.convert("L")
    image = ImageEnhance.Contrast(image).enhance(2.0)
    image = ImageEnhance.Sharpness(image).enhance(1.5)
    image = image.filter(ImageFilter.SHARPEN)
    return image


def ocr_image(image: Image.Image) -> str:
    image = preprocess_image_for_ocr(image)
    config = "--oem 3 --psm 6"

    try:
        return pytesseract.image_to_string(image, config=config).strip()
    except Exception as e:
        return f"OCR error: {str(e)}"


def extract_text_from_pdf(file_path: Path) -> str:
    text_parts = []

    try:
        doc = fitz.open(file_path)

        for page_number, page in enumerate(doc, start=1):
            page_text = page.get_text("text") or ""

            if len(page_text.strip()) > 100:
                text_parts.append(
                    f"\n--- PAGE {page_number} DIGITAL TEXT ---\n{page_text.strip()}"
                )

            pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            ocr_text = ocr_image(image)

            if ocr_text.strip():
                text_parts.append(
                    f"\n--- PAGE {page_number} OCR TEXT ---\n{ocr_text.strip()}"
                )

        doc.close()

    except Exception as e:
        text_parts.append(f"PDF extraction error: {str(e)}")

    return "\n".join(text_parts).strip()


def extract_text_from_image(file_path: Path) -> str:
    try:
        image = Image.open(file_path)
        return ocr_image(image)
    except Exception as e:
        return f"Image OCR error: {str(e)}"


def extract_text_from_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)

    if suffix in [".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"]:
        return extract_text_from_image(file_path)

    return ""


def get_case_sheet_file(db, case_id: int):
    return (
        db.query(CaseFile)
        .filter(
            CaseFile.case_id == case_id,
            CaseFile.file_type == "case_sheet"
        )
        .order_by(CaseFile.id.desc())
        .first()
    )


def get_lab_report_files(db, case_id: int):
    return (
        db.query(CaseFile)
        .filter(
            CaseFile.case_id == case_id,
            CaseFile.file_type == "lab_report"
        )
        .order_by(CaseFile.id.asc())
        .all()
    )


def get_all_case_files(db, case_id: int):
    return (
        db.query(CaseFile)
        .filter(CaseFile.case_id == case_id)
        .order_by(CaseFile.id.asc())
        .all()
    )


def process_case_background(case_id: int):
    db = SessionLocal()

    try:
        case = db.query(Case).filter(Case.id == case_id).first()

        if not case:
            return

        case.processing_status = "processing"
        db.commit()

        case_file = get_case_sheet_file(db, case_id)

        if not case_file:
            case.processing_status = "failed"
            case.ai_summary = {
                "extracted_facts": generate_structured_summary(""),
                "ai_reconstructed_case": {},
            }
            db.commit()
            return

        file_path = STORAGE_DIR / case_file.filename

        extracted_text = extract_text_from_file(file_path)

        confirmed_summary = generate_structured_summary(extracted_text)

        case.extracted_text = extracted_text

        lab_files = get_lab_report_files(db, case_id)

        for lab_file in lab_files:
            lab_path = STORAGE_DIR / lab_file.filename
            lab_text = extract_text_from_file(lab_path)
            lab_file.ai_analysis = analyze_lab_report_text(lab_text)

        db.flush()

        all_files = get_all_case_files(db, case_id)

        reconstruction = reconstruct_teaching_case(
            case_title=case.case_title,
            subject=case.subject,
            speciality=case.speciality,
            disease=case.disease,
            confirmed_summary=confirmed_summary,
            case_files=all_files,
        )

        case.ai_summary = {
            "extracted_facts": confirmed_summary,
            "ai_reconstructed_case": reconstruction,
        }

        case.processing_status = "completed"

        db.commit()

    except Exception as e:
        case = db.query(Case).filter(Case.id == case_id).first()

        if case:
            case.processing_status = "failed"
            case.ai_summary = {
                "extracted_facts": {
                    "case_type": "General Clinical Case",
                    "patient_history": "OCR or AI processing failed. Faculty review is required.",
                    "clinical_findings": "Not clearly documented.",
                    "clinical_significance": "The system could not complete OCR and AI structuring for this case.",
                    "planned_procedure": "Not clearly documented.",
                    "conclusion": "Processing failed. Check backend logs.",
                    "keywords": ["Processing failed"],
                    "structured_sections": {
                        "history_presenting_complaints": [
                            "Processing failed. Faculty review is required."
                        ],
                        "clinical_examination_diagnostics": [
                            "Not clearly documented."
                        ],
                        "management_treatment_plan": [
                            "Not clearly documented."
                        ]
                    },
                    "flowchart": [],
                    "qhub_questions": [],
                    "clinical_notes": [],
                    "error": str(e)
                },
                "ai_reconstructed_case": {
                    "reconstruction_error": str(e)
                }
            }
            db.commit()

    finally:
        db.close()
