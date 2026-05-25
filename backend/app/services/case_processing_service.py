from pathlib import Path
from sqlalchemy.orm import Session
import traceback

from app.db.database import SessionLocal

from app.models.case_model import Case
from app.models.case_file_model import CaseFile

from app.services.ocr_service import extract_text_with_fallback
from app.services.pdf_vision_extraction_service import extract_pdf_with_vision
from app.services.llm_service import generate_medical_summary
from app.services.clinical_notes_service import generate_clinical_notes
from app.services.lab_analysis_service import analyze_lab_report
from app.services.flowchart_generator_service import generate_flowchart_from_summary
from app.services.structured_summary_service import structure_clinical_summary

STORAGE_DIR = Path("storage")


def extract_text(filename: str):
    file_path = STORAGE_DIR / filename

    if file_path.suffix.lower() == ".pdf":
        print(f"Using Ollama Vision extraction for PDF: {file_path}")

        vision_result = extract_pdf_with_vision(
            str(file_path)
        )

        return vision_result.get(
            "merged_text",
            ""
        )

    print(f"Using OCR fallback extraction for non-PDF file: {file_path}")

    return extract_text_with_fallback(
        str(file_path)
    )


def normalize_list_result(result, key):
    if isinstance(result, list):
        return result

    if isinstance(result, dict):
        return result.get(key, [])

    return []


def process_case_background(case_id: int):
    db: Session = SessionLocal()

    try:
        case = db.query(Case).filter(
            Case.id == case_id
        ).first()

        if not case:
            return

        case.processing_status = "processing"
        db.commit()

        case_sheet = (
            db.query(CaseFile)
            .filter(
                CaseFile.case_id == case_id,
                CaseFile.file_type == "case_sheet"
            )
            .first()
        )

        if not case_sheet:
            case.processing_status = "failed"
            db.commit()
            return

        extracted_text = extract_text(
            case_sheet.filename
        )

        if not extracted_text:
            case.processing_status = "failed"
            db.commit()
            return

        ai_summary = generate_medical_summary(
            extracted_text,
            getattr(case, "department", ""),
            getattr(case, "super_specialty", "")
        )

        if not isinstance(ai_summary, dict):
            ai_summary = {}

        clinical_notes_result = generate_clinical_notes(
            extracted_text
        )

        clinical_notes = normalize_list_result(
            clinical_notes_result,
            "clinical_notes"
        )

        summary_for_flowchart = {
            **ai_summary,
            "clinical_notes": clinical_notes
        }

        flowchart = generate_flowchart_from_summary(
            summary_for_flowchart
        )

        if not isinstance(flowchart, list) or not flowchart:
            flowchart = [
                {
                    "step": "Patient Presentation",
                    "description": ai_summary.get(
                        "case_overview",
                        "Patient presentation reviewed."
                    ),
                    "type": "start"
                },
                {
                    "step": "Clinical Assessment",
                    "description": ai_summary.get(
                        "examination_and_findings",
                        "Clinical findings reviewed."
                    ),
                    "type": "assessment"
                },
                {
                    "step": "Management Plan",
                    "description": ai_summary.get(
                        "management_plan",
                        "Management plan reviewed."
                    ),
                    "type": "treatment"
                },
                {
                    "step": "Clinical Outcome",
                    "description": ai_summary.get(
                        "diagnosis_or_impression",
                        "Clinical conclusion reviewed."
                    ),
                    "type": "outcome"
                }
            ]

        structured_summary = structure_clinical_summary(ai_summary)

        combined_summary = {
            **ai_summary,
            "structured_summary": structured_summary,
            "clinical_notes": clinical_notes,
            "flowchart": flowchart
        }

        case.extracted_text = extracted_text
        case.ai_summary = combined_summary

        lab_reports = (
            db.query(CaseFile)
            .filter(
                CaseFile.case_id == case_id,
                CaseFile.file_type == "lab_report"
            )
            .all()
        )

        for lab in lab_reports:
            lab_text = extract_text(
                lab.filename
            )

            lab.ai_analysis = analyze_lab_report(
                lab_text
            )

        case.processing_status = "completed"

        db.commit()

        print(
            f"Case {case_id} processing completed successfully with auto flowchart"
        )

    except Exception:
        print("\n========== AI PROCESSING ERROR ==========")
        traceback.print_exc()
        print("=========================================\n")

        case = db.query(Case).filter(
            Case.id == case_id
        ).first()

        if case:
            case.processing_status = "failed"
            db.commit()

    finally:
        db.close()
