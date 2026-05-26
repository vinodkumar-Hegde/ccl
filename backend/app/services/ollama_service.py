import json
import re
import requests
from typing import Any, Dict

OLLAMA_URL = "http://host.docker.internal:11434/api/generate"
MODEL = "llama3"

SENSITIVE_MARKERS = [
    "hospital",
    "medical school",
    "promoted by",
    "admission form",
    "summary sheet",
    "mcts",
    "ipd",
    "registration",
    "aadhar",
    "aadhaar",
    "contact",
    "phone",
    "address",
    "name",
    "asha",
    "service provider",
    "signature",
    "patient name",
    "husband",
    "father",
]


def clean_ocr_text(text: str) -> str:
    if not text:
        return ""

    cleaned_lines = []

    hard_remove_markers = [
        "promoted by",
        "signature",
        "service provider",
        "patient name",
        "husband's / father's name",
        "address:",
        "phone",
        "aadhar",
        "aadhaar",
        "mcts",
        "ipd",
        "registration no",
        "reg. no",
    ]

    soft_noise_markers = [
        "hospital",
        "medical school",
        "name:",
    ]

    for line in text.splitlines():
        line = line.strip()
        lower = line.lower()

        if not line:
            continue

        if re.search(r"\b\d{10}\b", line):
            continue

        if re.search(r"\b\d{12}\b", line):
            continue

        if any(marker in lower for marker in hard_remove_markers):
            continue

        # Do not delete clinical lines just because they contain hospital/name words.
        # Only remove very short administrative/noise lines.
        if any(marker in lower for marker in soft_noise_markers) and len(line) < 80:
            continue

        # Remove obvious form-code lines.
        if re.search(r"GEMS[-/A-Z0-9]+", line, re.IGNORECASE):
            continue

        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\b\d{10}\b", " ", cleaned)
    cleaned = re.sub(r"\b\d{12}\b", " ", cleaned)
    cleaned = re.sub(r"[_^~`|{}[\]\\]+", " ", cleaned)
    cleaned = re.sub(r"[ ]{2,}", " ", cleaned)

    return cleaned.strip()


def extract_json(text: str):
    if not text:
        return None

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return None

    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return None


def has_sensitive_text(value: Any) -> bool:
    if not value:
        return False

    text = str(value).lower()
    marker_count = sum(1 for marker in SENSITIVE_MARKERS if marker in text)

    return (
        marker_count >= 2
        or re.search(r"\b\d{10}\b", text) is not None
        or re.search(r"\b\d{12}\b", text) is not None
    )


def bulletify(value):
    output = []

    def walk(item):
        if item is None:
            return

        if isinstance(item, str):
            clean = item.strip()
            if clean:
                output.append(clean)
            return

        if isinstance(item, dict):
            for key, val in item.items():
                label = str(key).strip()

                if isinstance(val, str):
                    clean_val = val.strip() or "Not clearly documented"
                    output.append(f"{label}: {clean_val}")
                elif isinstance(val, list):
                    for sub in val:
                        walk(sub)
                elif isinstance(val, dict):
                    for sub_key, sub_val in val.items():
                        output.append(f"{label} - {sub_key}: {sub_val}")
                else:
                    output.append(f"{label}: {val}")
            return

        if isinstance(item, list):
            for sub in item:
                walk(sub)
            return

        output.append(str(item))

    walk(value)

    cleaned = []
    for item in output:
        item = item.strip()
        if item and item not in cleaned and not has_sensitive_text(item):
            cleaned.append(item)

    return cleaned


def select_relevant_clinical_text(cleaned: str, max_chars: int = 12000) -> str:
    """
    Select clinically meaningful OCR lines from the whole document.
    This avoids sending only the first pages/admin pages to Ollama.
    """
    if not cleaned:
        return ""

    high_value_keywords = [
        "chief complaint",
        "complaints",
        "presenting complaint",
        "history of present illness",
        "past history",
        "treatment history",
        "personal history",
        "family history",
        "menstrual history",
        "obstetric history",
        "birth history",
        "developmental history",
        "immunization",
        "physical examination",
        "general examination",
        "systemic examination",
        "pallor",
        "icterus",
        "cyanosis",
        "clubbing",
        "lymphadenopathy",
        "edema",
        "malnutrition",
        "dehydration",
        "diagnosis",
        "provisional diagnosis",
        "final diagnosis",
        "investigation",
        "blood",
        "hb",
        "platelet",
        "sugar",
        "creatinine",
        "bilirubin",
        "sgot",
        "sgpt",
        "x-ray",
        "ct",
        "mri",
        "usg",
        "ecg",
        "treatment",
        "management",
        "procedure",
        "surgery",
        "operation",
        "surgeries",
        "discharge",
        "advice",
        "plan",
    ]

    low_value_keywords = [
        "great eastern medical school",
        "promoted by",
        "patient's name",
        "patient name",
        "signature",
        "registration",
        "ip no",
        "ip.no",
        "address",
        "phone",
        "aadhar",
        "gems-sklm",
    ]

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]

    selected = []
    context_window = 4

    for idx, line in enumerate(lines):
        lower = line.lower()

        if any(bad in lower for bad in low_value_keywords) and len(line) < 120:
            continue

        if any(key in lower for key in high_value_keywords):
            start = max(0, idx - 1)
            end = min(len(lines), idx + context_window + 1)

            for item in lines[start:end]:
                item_lower = item.lower()

                if any(bad in item_lower for bad in low_value_keywords) and len(item) < 120:
                    continue

                if item not in selected:
                    selected.append(item)

    # If nothing was selected, fall back to full cleaned text.
    if not selected:
        selected_text = cleaned
    else:
        selected_text = "\n".join(selected)

    # Add a tail sample also, because discharge summaries are often at the end.
    tail = cleaned[-4000:] if len(cleaned) > 4000 else ""

    final_text = selected_text + "\n\n--- DOCUMENT END SAMPLE ---\n" + tail

    return final_text[:max_chars]


def fallback_summary(error: str = "") -> Dict[str, Any]:
    return {
        "case_type": "General Clinical Case",
        "patient_history": (
            "Clinical record reviewed after removing sensitive identifiers. "
            "Detailed patient history is not clearly documented due to OCR limitations."
        ),
        "clinical_findings": (
            "Specific clinical findings are not clearly documented in the extracted document."
        ),
        "clinical_significance": (
            "This case requires structured clinical review and faculty verification before publication."
        ),
        "planned_procedure": "Not clearly documented.",
        "conclusion": (
            "Structured de-identified clinical summary generated. Raw OCR and sensitive identifiers were not exposed."
        ),
        "keywords": ["Clinical case", "Documentation review", "Faculty verification"],
        "structured_sections": {
            "history_presenting_complaints": [
                "History and presenting complaints are not clearly documented."
            ],
            "clinical_examination_diagnostics": [
                "Clinical examination and diagnostic findings are not clearly documented."
            ],
            "management_treatment_plan": [
                "Management or treatment plan is not clearly documented."
            ]
        },
        "flowchart": [],
        "qhub_questions": [],
        "clinical_notes": [],
        "llm_error": error,
    }


def normalize_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    fallback = fallback_summary()

    if not isinstance(data, dict):
        return fallback

    def safe_text(key):
        value = data.get(key)
        if not value:
            return fallback[key]
        if has_sensitive_text(value):
            return fallback[key]
        return str(value).strip()

    structured = data.get("structured_sections")
    if not isinstance(structured, dict):
        structured = fallback["structured_sections"]

    structured_clean = {
        "history_presenting_complaints": bulletify(
            structured.get("history_presenting_complaints")
        ) or fallback["structured_sections"]["history_presenting_complaints"],

        "clinical_examination_diagnostics": bulletify(
            structured.get("clinical_examination_diagnostics")
        ) or fallback["structured_sections"]["clinical_examination_diagnostics"],

        "management_treatment_plan": bulletify(
            structured.get("management_treatment_plan")
        ) or fallback["structured_sections"]["management_treatment_plan"],
    }

    return {
        "case_type": data.get("case_type") or fallback["case_type"],
        "patient_history": safe_text("patient_history"),
        "clinical_findings": safe_text("clinical_findings"),
        "clinical_significance": safe_text("clinical_significance"),
        "planned_procedure": safe_text("planned_procedure"),
        "conclusion": safe_text("conclusion"),
        "keywords": data.get("keywords") if isinstance(data.get("keywords"), list) else fallback["keywords"],
        "structured_sections": structured_clean,
        "flowchart": data.get("flowchart") if isinstance(data.get("flowchart"), list) else [],
        "qhub_questions": data.get("qhub_questions") if isinstance(data.get("qhub_questions"), list) else [],
        "clinical_notes": data.get("clinical_notes") if isinstance(data.get("clinical_notes"), list) else [],
    }


def clean_clinical_bullet(line: str) -> str:
    if not line:
        return ""

    line = str(line).strip()
    line = re.sub(r"\s+", " ", line)
    line = line.replace("•", "").strip()

    # Remove page/form codes
    if re.search(r"GEMS[-/A-Z0-9]+", line, re.IGNORECASE):
        return ""

    # Remove empty form labels without values
    empty_labels = [
        "operative procedures / treatment notes",
        "operative procedures /treatment notes",
        "date & time of discharge",
        "discharge status",
        "final diagnosis",
        "treatment history",
        "family planning methods used",
        "familyplannii methodsused",
    ]

    lower = line.lower().strip(" :.-")

    for label in empty_labels:
        if lower == label or lower == f"{label}:":
            return ""

    # Remove lines that are mostly symbols/checkbox noise
    alpha_count = sum(ch.isalpha() for ch in line)
    if alpha_count < 5:
        return ""

    # Normalize common headings
    replacements = {
        "4.treatment history": "Treatment history section is present.",
        "4. treatment history": "Treatment history section is present.",
        "personalhistory": "Personal history section is present.",
        "family history.": "Family history section is present.",
        "physicalexamination": "Physical examination section is present.",
    }

    low = line.lower()
    for bad, good in replacements.items():
        if bad in low:
            return good

    return line


def clean_bullet_list(items, max_items=10):
    cleaned = []

    for item in items or []:
        line = clean_clinical_bullet(item)

        if not line:
            continue

        if has_sensitive_text(line):
            continue

        if line not in cleaned:
            cleaned.append(line)

        if len(cleaned) >= max_items:
            break

    return cleaned


def deterministic_clinical_summary(cleaned: str) -> Dict[str, Any]:
    selected = select_relevant_clinical_text(cleaned, max_chars=18000)

    lines = [line.strip() for line in selected.splitlines() if line.strip()]

    skip_patterns = [
        r"^[-–—]+$",
        r"great eastern medical",
        r"promoted by",
        r"patient'?s name",
        r"gems[-/]",
        r"fot mrd use only",
        r"familyplannii",
        r"family planning methodsused\s*[:.]?$",
        r"ageatmarriage.*family planning",
        r"notapplicable",
        r"notapplicable",
        r"date\s*&\s*time\s*of\s*discharge\s*[:.]?$",
        r"operative procedures\s*/?\s*treatment notes\s*[:.]?$",
        r"final diagnosis\s*[:.]?$",
        r"discharge status\s*[:.]?$",
    ]

    def is_noise(line: str) -> bool:
        low = line.lower().strip()
        if len(low) < 4:
            return True

        alpha_count = sum(ch.isalpha() for ch in line)
        if alpha_count < 5:
            return True

        for pattern in skip_patterns:
            if re.search(pattern, low):
                return True

        # Remove checkbox/template fragments without meaningful selected value
        if re.search(r"\b(no|yes)\b.*\b(no|yes)\b", low) and len(low) < 80:
            return True

        # Remove section numbering headings like 4.TREATMENT HISTORY
        if re.search(r"^\d+(\.\d+)?\s*\.?\s*[a-z /()&-]+\s*[:.-]?$", low):
            return True

        # Remove short empty form labels like Pallor-, Icterus*, Height:
        if re.search(r"^[0-9.\s]*[a-z /()&-]{3,25}\s*[:*\-]$", low):
            return True

        # Remove OCR fragments with no clinical value
        if low in ["plantars q", "plan of care:", "planof care: =a"]:
            return True

        return False

    def clean_line(line: str) -> str:
        line = str(line).strip()
        line = re.sub(r"\s+", " ", line)
        line = line.replace("•", "").strip()
        line = re.sub(r"^[,.;:\-\s]+", "", line)
        line = re.sub(r"\s+:", ":", line)

        if is_noise(line):
            return ""

        if has_sensitive_text(line):
            return ""

        # If final diagnosis is unreadable OCR, mark it safely.
        if "final diagnosis" in line.lower():
            value = line.split(":", 1)[-1].strip() if ":" in line else ""
            readable_words = re.findall(r"[A-Za-z]{3,}", value)

            if len(readable_words) < 3:
                return "Final diagnosis is present but requires faculty verification due to unclear handwriting/OCR."

            return "Final diagnosis is present but unreadable/uncertain in OCR; requires faculty verification."

        if "operative procedures" in line.lower() or "treatment notes" in line.lower():
            value = line.split(":", 1)[-1].strip() if ":" in line else ""
            if len(value) < 4:
                return ""
            return "Operative/treatment note is present but unreadable/uncertain in OCR; requires faculty verification."

        if "discharge status" in line.lower():
            if any(word in line.lower() for word in ["cured", "recovered", "improved", "not recovered", "referred"]):
                return "Discharge status field is present; selected status requires faculty verification."
            return ""

        return line

    history_keywords = [
        "treatment history",
        "diabetes",
        "hypertension",
        "cad",
        "asthma",
        "tuberculosis",
        "antibiotics",
        "hormones",
        "chemo",
        "radiation",
        "blood transfusion",
        "surgeries",
        "personal history",
        "appetite",
        "diet",
        "bowels",
        "micturition",
        "allergies",
        "habits",
        "alcohol",
        "tobacco",
        "drug use",
        "betel",
        "family history",
        "heart disease",
        "stroke",
        "cancers",
        "psychiatric",
        "sibling",
        "menstrual history",
        "obstetric history",
        "gravida",
        "para",
        "lmp",
    ]

    exam_keywords = [
        "physical examination",
        "height",
        "weight",
        "mac",
        "hc",
        "bmi",
        "body surface",
        "pallor",
        "icterus",
        "cyanosis",
        "clubbing",
        "lymphadenopathy",
        "oedema",
        "edema",
        "malnutrition",
        "dehydration",
        "birth history",
        "developmental history",
        "immunization",
        "plantars",
        "flexor",
        "extensor",
        "equivocal",
        "unelicitable",
    ]

    management_keywords = [
        "final diagnosis",
        "operative procedures",
        "treatment notes",
        "discharge status",
        "management",
        "procedure",
        "operation",
        "discharge advice",
        "advice",
        "plan",
    ]

    def collect(keys, max_items=10):
        picked = []

        for line in lines:
            low = line.lower()

            if any(k in low for k in keys):
                clean = clean_line(line)

                if clean and clean not in picked:
                    picked.append(clean)

            if len(picked) >= max_items:
                break

        return picked

    history = collect(history_keywords, max_items=12)
    exam = collect(exam_keywords, max_items=12)
    management = collect(management_keywords, max_items=8)

    # Add stronger interpreted bullets when only template headings are detected.
    selected_lower = selected.lower()

    interpreted_history = []

    if "treatment history" in selected_lower:
        interpreted_history.append(
            "Treatment history section is present with fields for diabetes, hypertension, CAD, asthma, tuberculosis, antibiotics, hormones, chemo/radiation, blood transfusion and previous surgeries; exact positive entries require faculty verification."
        )

    if "personalhistory" in selected_lower or "personal history" in selected_lower:
        interpreted_history.append(
            "Personal history section is present with appetite, diet, bowel, micturition, allergy and habits/addictions fields; exact entries require verification."
        )

    if "family history" in selected_lower:
        interpreted_history.append(
            "Family history section is present with diabetes, hypertension, heart disease, stroke, cancers, tuberculosis and asthma fields; selected findings require verification."
        )

    interpreted_exam = []

    if "physicalexamination" in selected_lower or "physical examination" in selected_lower:
        interpreted_exam.append(
            "Physical examination section is present with height, weight, MAC, BMI, pallor, icterus, cyanosis, clubbing, lymphadenopathy, oedema, malnutrition and dehydration fields."
        )

    if "developmental history" in selected_lower:
        interpreted_exam.append(
            "Developmental history section is present; normal/abnormal status requires verification."
        )

    if "immunization status" in selected_lower:
        interpreted_exam.append(
            "Immunization status section is present; up-to-date status requires verification."
        )

    # Prefer interpreted clinical bullets over noisy raw OCR.
    history = interpreted_history + [x for x in history if x not in interpreted_history]
    exam = interpreted_exam + [x for x in exam if x not in interpreted_exam]

    # Keep management only if meaningful.
    management = [
        x for x in management
        if not re.search(
            r"family planning|ageatmarriage|treatment history section|plantars|flexor|extensor|equivocal|unelicitable|plan of care|planof care|plan of primary consultant|^procedure$|access and fluids planned|before patient leaves operation room",
            x.lower()
        )
    ]

    def keep_only_meaningful(items, section):
        safe = []

        for item in items:
            low = item.lower().strip()

            # Always keep interpreted summary bullets
            if "section is present" in low or "requires faculty verification" in low:
                safe.append(item)
                continue

            # Remove raw OCR template/vital/checklist fragments
            noisy_patterns = [
                r"^\d+\.\s*[a-z ]+\s*:",
                r"mac:",
                r"bmi:",
                r"body surface",
                r"pallor-",
                r"clubbing",
                r"pulserate",
                r"respiration",
                r"temperature",
                r"flexor",
                r"extensor",
                r"dwno",
                r"dyes",
                r"cyno",
                r"countforfullmin",
                r"mg/dl",
                r"^procedure$",
                r"access and fluids planned",
                r"before patient leaves operation room",
            ]

            if any(re.search(pattern, low) for pattern in noisy_patterns):
                continue

            # Keep diagnosis/procedure only if explicitly marked for verification
            if section == "management":
                if "final diagnosis documented" in low or "operative/treatment note" in low or "discharge status" in low:
                    safe.append(item)
                continue

            # For history/exam, avoid raw OCR fragments; interpreted bullets are enough
            if len(item) > 80 and not has_sensitive_text(item):
                safe.append(item)

        # Remove duplicates
        final = []
        for item in safe:
            if item not in final:
                final.append(item)

        return final

    history = keep_only_meaningful(history, "history")
    exam = keep_only_meaningful(exam, "exam")
    management = keep_only_meaningful(management, "management")

    if not history:
        history = ["History fields are present in the case sheet, but exact clinical entries require faculty verification."]

    if not exam:
        exam = ["Clinical examination/diagnostic fields are present, but exact values require verification from the scanned sheet."]

    if not management:
        management = ["Final diagnosis/procedure/discharge details are either unclear or require faculty verification from the scanned sheet."]

    case_type = "General Clinical Case"

    surgical_terms = [
        "surg_case",
        "surgical",
        "operative procedures",
        "operation room",
        "procedure",
        "access and fluids planned",
        "before patient leaves operation room",
    ]

    obg_positive_terms = [
        "pregnancy",
        "pregnant",
        "labour pain",
        "labor pain",
        "active labour",
        "lscs",
        "caesarean",
        "cesarean",
        "antenatal",
        "postnatal",
        "fetal distress",
        "foetal distress",
        "delivery conducted",
        "delivered a",
    ]

    # Surgical classification gets priority because generic case-sheet templates
    # may contain menstrual/obstetric fields even for non-OBG cases.
    if any(word in selected_lower for word in surgical_terms):
        case_type = "Surgical Clinical Case"
    elif any(word in selected_lower for word in obg_positive_terms):
        case_type = "Obstetric / Gynecological Clinical Case"

    return {
        "case_type": case_type,
        "patient_history": "The uploaded case sheet contains treatment history, personal history and family history sections. Most checkbox/handwritten entries require faculty verification because OCR confidence is limited.",
        "clinical_findings": "The document contains physical examination and clinical checklist fields. Exact positive findings should be verified manually from the scanned sheet.",
        "clinical_significance": "This case is suitable for structured clinical documentation review, but OCR-derived findings must be validated before publication.",
        "planned_procedure": "Procedure/treatment details are not reliably readable from OCR and require faculty verification.",
        "conclusion": "A de-identified structured summary was generated from the scanned case sheet. Faculty review is recommended before publishing.",
        "keywords": [
            "Clinical case",
            "Surgical case sheet",
            "Treatment history",
            "Physical examination",
            "Faculty verification"
        ],
        "structured_sections": {
            "history_presenting_complaints": history[:12],
            "clinical_examination_diagnostics": exam[:12],
            "management_treatment_plan": management[:8]
        },
        "flowchart": [
            {
                "step": "Case sheet upload",
                "description": "Scanned clinical case sheet uploaded and OCR processed."
            },
            {
                "step": "History review",
                "description": "Treatment, personal and family history fields identified."
            },
            {
                "step": "Examination review",
                "description": "Physical examination and checklist fields identified."
            },
            {
                "step": "Faculty verification",
                "description": "Handwritten/checkbox entries require manual validation."
            }
        ],
        "qhub_questions": [
            {
                "type": "Clinical Review",
                "question": "Which history fields are clinically positive after faculty verification?"
            },
            {
                "type": "Examination",
                "question": "Which physical examination findings are clearly positive?"
            },
            {
                "type": "Management",
                "question": "What is the verified final diagnosis and treatment/procedure plan?"
            }
        ],
        "clinical_notes": []
    }


def generate_structured_summary(text: str) -> Dict[str, Any]:
    cleaned = clean_ocr_text(text)

    if not cleaned or len(cleaned) < 20:
        return fallback_summary("OCR text was too short after privacy cleaning.")

    prompt = f"""
You are a senior clinical documentation expert.

You will receive noisy OCR text from a scanned medical case sheet.

Your task:
- Identify what type of clinical case this is.
- Do not assume it is obstetrics.
- Do not force obstetric sections unless the OCR clearly indicates obstetrics, pregnancy, labour, LSCS, delivery, gravida, para, fetus, or antenatal record.
- Convert noisy OCR into a clean academic clinical case summary.
- Never copy raw OCR lines directly.
- Never expose patient identifiers or hospital identifiers.

STRICT PRIVACY RULES:
Do not include:
- patient name
- hospital name
- address
- phone number
- Aadhaar number
- registration number
- IPD number
- MCTS number
- doctor/staff names
- signatures

EXTRACTION RULES:
Extract only clinically meaningful content:
- presenting complaints
- relevant history
- clinical examination
- vitals if readable
- investigations
- imaging
- diagnosis/impression
- treatment/procedure/management
- clinical significance
- teaching points
- conclusion

If information is unclear, write "requires verification" or "not clearly documented".
Do not hallucinate exact values that are not present.

Return JSON only in this exact structure:

{{
  "case_type": "",
  "patient_history": "",
  "clinical_findings": "",
  "clinical_significance": "",
  "planned_procedure": "",
  "conclusion": "",
  "keywords": [],
  "structured_sections": {{
    "history_presenting_complaints": [],
    "clinical_examination_diagnostics": [],
    "management_treatment_plan": []
  }},
  "flowchart": [
    {{
      "step": "",
      "description": ""
    }}
  ],
  "qhub_questions": [
    {{
      "type": "",
      "question": ""
    }}
  ],
  "clinical_notes": []
}}

Important:
Each item inside structured_sections must be a STRING.

DE-IDENTIFIED CLINICALLY RELEVANT OCR TEXT:
{select_relevant_clinical_text(cleaned)}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 1800
                }
            },
            timeout=120,
        )

        response.raise_for_status()
        raw = response.json().get("response", "")
        parsed = extract_json(raw)

        if not parsed:
            return deterministic_clinical_summary(cleaned)

        normalized = normalize_summary(parsed)

        sections = normalized.get("structured_sections", {})
        weak_output = (
            "not clearly documented" in str(sections).lower()
            and "not clearly documented" in str(normalized.get("patient_history", "")).lower()
        )

        if weak_output:
            return deterministic_clinical_summary(cleaned)

        return normalized

    except Exception as e:
        return fallback_summary(str(e))
