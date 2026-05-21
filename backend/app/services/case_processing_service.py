from pathlib import Path
from sqlalchemy.orm import Session
import traceback

from app.db.database import SessionLocal

from app.models.case_model import Case
from app.models.case_file_model import CaseFile

from app.services.ocr_service import (
    extract_text_with_fallback
)

from app.services.llm_service import (
    generate_medical_summary
)

from app.services.clinical_notes_service import (
    generate_clinical_notes
)

from app.services.flowchart_service import (
    generate_flowchart
)

from app.services.lab_analysis_service import (
    analyze_lab_report
)

STORAGE_DIR = Path("storage")


def extract_text(filename: str):
    file_path = STORAGE_DIR / filename

    return extract_text_with_fallback(
        str(file_path)
    )


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
            extracted_text
        )

        clinical_notes_result = generate_clinical_notes(
            extracted_text
        )

        if isinstance(clinical_notes_result, list):
            clinical_notes = clinical_notes_result
        else:
            clinical_notes = clinical_notes_result.get(
                "clinical_notes",
                []
            )

        flowchart_result = generate_flowchart(
            extracted_text
        )

        if isinstance(flowchart_result, list):
            flowchart = flowchart_result
        else:
            flowchart = flowchart_result.get(
                "flowchart",
                []
            )

        combined_summary = {
            **ai_summary,
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
            f"Case {case_id} processing completed successfully"
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