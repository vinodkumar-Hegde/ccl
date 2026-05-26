import re

from app.services.document_classifier_service import detect_document_type


COMMON_NOISE = [
    "great eastern medical school",
    "promoted by aditya",
    "gems-sklm",
    "please write",
    "signed and stamped",
    "doctor's authorization",
    "name & signature",
    "signature of",
    "witnessing nurse",
    "administering nurse",
    "form",
]


DOCUMENT_KEYWORDS = {
    "obg_case_sheet": [
        "admission form", "summary sheet", "obstetric history", "gravida",
        "para", "complaints", "present pregnancy", "high risk", "obstetric examination",
        "investigations", "delivery notes", "lscs", "operation notes",
        "procedure notes", "baby notes", "birth weight", "final diagnosis",
        "provisional diagnosis", "indication", "findings", "treatment advised"
    ],
    "general_clinical_case_sheet": [
        "history", "complaints", "examination", "investigation", "diagnosis",
        "treatment", "plan", "progress", "doctor's orders"
    ],
    "lab_report": [
        "hb", "rbc", "wbc", "platelet", "creatinine", "urea", "bilirubin",
        "sgot", "sgpt", "sodium", "potassium", "rbs", "fbs", "hba1c", "thyroid"
    ],
    "discharge_summary": [
        "discharge summary", "date of admission", "date of discharge",
        "diagnosis", "hospital course", "treatment", "condition at discharge",
        "discharge advice", "follow up"
    ],
    "operation_notes": [
        "operation notes", "procedure notes", "surgeon", "anaesthetist",
        "anaesthesia", "indication", "incision", "findings", "procedure performed",
        "treatment advised"
    ],
    "medication_chart": [
        "drug", "dose", "route", "frequency", "medication", "prescription",
        "iv fluid", "infusion"
    ],
    "lecture_mcq_pdf": [
        "q1", "q 1", "question", "a.", "b.", "c.", "d.", "answer",
        "ophthalmology", "fmge", "neet", "mcq"
    ],
    "unknown": [
        "history", "examination", "investigation", "diagnosis", "treatment",
        "summary", "procedure", "findings"
    ],
}


def _clean_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"\s+", " ", line)
    line = re.sub(r"[•·]{2,}", " ", line)
    line = re.sub(r"[_\-]{3,}", " ", line)
    return line.strip()


def _is_symbol_noise(line: str) -> bool:
    if not line or len(line) <= 1:
        return True

    letters = sum(ch.isalpha() for ch in line)
    digits = sum(ch.isdigit() for ch in line)
    useful = letters + digits

    return useful / max(len(line), 1) < 0.22


def _split_pages(text: str):
    parts = re.split(r"\n\s*PAGE\s+\d+\s*\n", text, flags=re.IGNORECASE)

    if len(parts) <= 1:
        parts = re.split(r"(?=GREAT EASTERN MEDICAL SCHOOL|DISCHARGE SUMMARY|OPERATION NOTES|PROGRESS RECORD)", text, flags=re.IGNORECASE)

    return [part.strip() for part in parts if part.strip()]


def _page_score(page_text: str, document_type: str) -> int:
    low = page_text.lower()
    keywords = DOCUMENT_KEYWORDS.get(document_type, DOCUMENT_KEYWORDS["unknown"])

    score = 0

    for keyword in keywords:
        if keyword in low:
            score += 5

    for noise in COMMON_NOISE:
        if noise in low:
            score -= 1

    # preserve pages with many clinical numeric values
    if re.search(r"\b(hb|platelet|rbs|fbs|creatinine|bilirubin|sgot|sgpt|bp|pulse|fhr)\b", low):
        score += 8

    return score


def deidentify_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"great eastern medical school\s*&?\s*hospital", "[Hospital name removed]", text, flags=re.IGNORECASE)
    text = re.sub(r"promoted by\s+[a-z\s]+society", "[Institution details removed]", text, flags=re.IGNORECASE)
    text = re.sub(r"patient\s*name\s*[:\-]?\s*[^\n]+", "Patient name: [Removed]", text, flags=re.IGNORECASE)
    text = re.sub(r"name\s*[:\-]?\s*[^\n]{2,80}", "Name: [Removed]", text, flags=re.IGNORECASE)
    text = re.sub(r"address\s*[:\-]?\s*[^\n]+", "Address: [Removed]", text, flags=re.IGNORECASE)
    text = re.sub(r"ph\s*no\.?\s*[:\-]?\s*[^\n]+", "Phone: [Removed]", text, flags=re.IGNORECASE)

    return text


def clean_extracted_clinical_text(raw_text: str) -> tuple[str, dict]:
    if not raw_text:
        return "", {
            "document_type": "unknown",
            "department": "general",
        }

    metadata = detect_document_type(raw_text)
    document_type = metadata["document_type"]

    raw_text = deidentify_text(raw_text)
    pages = _split_pages(raw_text)

    scored_pages = []

    for index, page in enumerate(pages, start=1):
        scored_pages.append((_page_score(page, document_type), index, page))

    selected = [item for item in scored_pages if item[0] >= 4]

    if not selected:
        selected = sorted(scored_pages, reverse=True)[:12]
    else:
        selected = sorted(selected, reverse=True)[:18]

    selected = sorted(selected, key=lambda item: item[1])

    cleaned_blocks = []

    for score, page_no, page_text in selected:
        lines = []

        for line in page_text.splitlines():
            line = _clean_line(line)

            if not line:
                continue

            if _is_symbol_noise(line):
                continue

            low = line.lower()

            if any(noise in low for noise in COMMON_NOISE):
                continue

            lines.append(line)

        block = "\n".join(lines).strip()

        if block:
            cleaned_blocks.append(f"PAGE {page_no} | SCORE {score}\n{block}")

    cleaned_text = "\n\n".join(cleaned_blocks)

    seen = set()
    unique_lines = []

    for line in cleaned_text.splitlines():
        key = line.lower().strip()

        if key in seen:
            continue

        seen.add(key)
        unique_lines.append(line)

    cleaned_text = "\n".join(unique_lines)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()

    return cleaned_text, metadata


def build_llm_ready_case_text(raw_text: str) -> str:
    cleaned, metadata = clean_extracted_clinical_text(raw_text)

    document_type = metadata.get("document_type", "unknown")
    department = metadata.get("department", "general")

    if not cleaned:
        cleaned = raw_text or ""

    return f"""
DOCUMENT TYPE: {document_type}
DEPARTMENT: {department}

TASK:
Create the correct structured output based on the detected document type.

RULES:
- Do not assume all documents are OBG.
- Do not assume all documents are clinical case sheets.
- If the document is a clinical case sheet, summarize history, findings, investigations, diagnosis/impression, and management.
- If it is a discharge summary, summarize admission, diagnosis, hospital course, treatment, discharge advice, and follow-up.
- If it is a lab report, extract abnormal values and clinical interpretation.
- If it is an operation/procedure note, extract indication, procedure, findings, outcome, and treatment advised.
- If it is an MCQ/lecture PDF, extract questions, options, answers if visible, and explanation.
- Ignore hospital headers, form numbers, consent boilerplate, blank charts, and repeated templates.
- Use only facts visible in the OCR text.
- If a specific value is unclear, write "Not clearly readable".

CLEANED OCR TEXT:
{cleaned[:18000]}
""".strip()
