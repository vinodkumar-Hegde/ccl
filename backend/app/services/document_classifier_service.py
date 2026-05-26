import re


def _count_keywords(text: str, keywords: list[str]) -> int:
    low = (text or "").lower()
    return sum(1 for keyword in keywords if keyword in low)


DOCUMENT_TYPE_KEYWORDS = {
    "obg_case_sheet": [
        "obstetric", "gravida", "para", "lscs", "caesarean", "cesarean",
        "delivery", "baby", "birth weight", "fhr", "partograph",
        "antenatal", "pregnancy", "puerperium", "bishop score"
    ],
    "general_clinical_case_sheet": [
        "clinical record", "progress record", "doctor's orders",
        "history", "examination", "diagnosis", "treatment",
        "investigation", "plan", "chief complaints", "present illness"
    ],
    "lab_report": [
        "hb", "platelet", "rbc", "wbc", "creatinine", "urea",
        "bilirubin", "sgot", "sgpt", "sodium", "potassium",
        "blood sugar", "hba1c", "thyroid", "report"
    ],
    "discharge_summary": [
        "discharge summary", "date of admission", "date of discharge",
        "condition at discharge", "discharge advice", "follow up",
        "hospital course"
    ],
    "operation_notes": [
        "operation notes", "procedure notes", "operative procedure",
        "surgeon", "anaesthetist", "anaesthesia", "incision",
        "findings", "procedure performed"
    ],
    "medication_chart": [
        "regular drug prescriptions", "drug chart", "dose", "route",
        "frequency", "drug name", "medication", "prescription"
    ],
    "lecture_mcq_pdf": [
        "q1", "q 1", "question", "option", "a.", "b.", "c.", "d.",
        "mcq", "fmge", "neet", "answer", "tutorials"
    ],
}


DEPARTMENT_KEYWORDS = {
    "obstetrics_and_gynaecology": [
        "obstetric", "gynae", "pregnancy", "delivery", "lscs", "caesarean",
        "gravida", "para", "baby", "fhr", "partograph"
    ],
    "ophthalmology": [
        "ophthalmology", "eye", "retina", "proptosis", "chemosis",
        "lid retraction", "astigmatism", "myopic", "hypermetropic"
    ],
    "cardiology": [
        "ecg", "echo", "chest pain", "troponin", "myocardial",
        "angiography", "pci", "cabg"
    ],
    "medicine": [
        "fever", "diabetes", "hypertension", "asthma", "thyroid",
        "renal", "liver", "infection", "sepsis"
    ],
    "surgery": [
        "surgery", "operation", "incision", "laparotomy", "appendix",
        "hernia", "operative"
    ],
    "pediatrics": [
        "pediatric", "paediatric", "child", "neonate", "birth weight",
        "immunization", "nicu"
    ],
}


def detect_document_type(raw_text: str) -> dict:
    text = raw_text or ""

    type_scores = {
        doc_type: _count_keywords(text, keywords)
        for doc_type, keywords in DOCUMENT_TYPE_KEYWORDS.items()
    }

    department_scores = {
        department: _count_keywords(text, keywords)
        for department, keywords in DEPARTMENT_KEYWORDS.items()
    }

    document_type = max(type_scores, key=type_scores.get)
    department = max(department_scores, key=department_scores.get)

    if type_scores[document_type] == 0:
        document_type = "unknown"

    if department_scores[department] == 0:
        department = "general"

    # Strong override rules
    low = text.lower()

    if "discharge summary" in low:
        document_type = "discharge_summary"

    if "operation notes" in low or "procedure notes" in low:
        document_type = "operation_notes"

    if "regular drug prescriptions" in low or "drug chart" in low:
        document_type = "medication_chart"

    if re.search(r"\bq\s*1\b|\bq1\b", low) and ("a." in low or "b." in low):
        document_type = "lecture_mcq_pdf"

    if "lscs" in low or "gravida" in low or "partograph" in low:
        document_type = "obg_case_sheet"
        department = "obstetrics_and_gynaecology"

    return {
        "document_type": document_type,
        "department": department,
        "type_scores": type_scores,
        "department_scores": department_scores,
    }
