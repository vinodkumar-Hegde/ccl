import json
import re
import requests
from typing import Any, Dict

OLLAMA_URL = "http://host.docker.internal:11434/api/generate"
MODEL = "llama3"


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


def clean_lab_ocr(text: str) -> str:
    if not text:
        return ""

    sensitive_markers = [
        "patient name",
        "name:",
        "hospital",
        "address",
        "phone",
        "mobile",
        "registration",
        "ip no",
        "uhid",
        "doctor",
        "consultant",
        "sample id",
        "barcode",
    ]

    cleaned_lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        lower = line.lower()

        if any(marker in lower for marker in sensitive_markers) and len(line) < 140:
            continue

        if re.search(r"\b\d{10}\b", line):
            continue

        if re.search(r"\b\d{12}\b", line):
            continue

        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\b\d{10}\b", " ", cleaned)
    cleaned = re.sub(r"\b\d{12}\b", " ", cleaned)

    return cleaned.strip()


def deterministic_lab_fallback(text: str) -> Dict[str, Any]:
    cleaned = clean_lab_ocr(text)

    common_tests = [
        "hemoglobin", "haemoglobin", "hb", "wbc", "rbc", "platelet",
        "neutrophils", "lymphocytes", "eosinophils", "monocytes",
        "basophils", "esr", "crp", "urea", "creatinine",
        "sodium", "potassium", "chloride", "bilirubin",
        "sgot", "sgpt", "ast", "alt", "alkaline phosphatase",
        "albumin", "globulin", "glucose", "fbs", "ppbs",
        "hba1c", "cholesterol", "triglycerides", "hdl", "ldl",
        "tsh", "t3", "t4"
    ]

    extracted = []

    for line in cleaned.splitlines():
        lower = line.lower()

        if any(test in lower for test in common_tests):
            extracted.append({
                "test_name": line,
                "value": "Requires verification",
                "unit": "",
                "reference_range": "",
                "interpretation": "Possible lab parameter detected by OCR. Value requires verification from original report."
            })

    if not extracted:
        extracted = [{
            "test_name": "Lab report content",
            "value": "Not clearly readable",
            "unit": "",
            "reference_range": "",
            "interpretation": "Lab report OCR was unclear. Manual verification is required."
        }]

    return {
        "report_type": "Lab Report",
        "source_confidence": "low",
        "extracted_tests": extracted[:30],
        "abnormal_findings": [],
        "clinical_summary": "Lab report processed from uploaded image/PDF. Values require verification against the original report.",
        "faculty_verification_required": True
    }


def normalize_lab_analysis(data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    fallback = deterministic_lab_fallback(raw_text)

    if not isinstance(data, dict):
        return fallback

    tests = data.get("extracted_tests")

    if not isinstance(tests, list) or not tests:
        tests = fallback["extracted_tests"]

    clean_tests = []

    for item in tests:
        if isinstance(item, dict):
            clean_tests.append({
                "test_name": str(item.get("test_name") or item.get("name") or "Unknown test"),
                "value": str(item.get("value") or "Requires verification"),
                "unit": str(item.get("unit") or ""),
                "reference_range": str(item.get("reference_range") or ""),
                "interpretation": str(item.get("interpretation") or "Requires verification")
            })
        elif isinstance(item, str):
            clean_tests.append({
                "test_name": item,
                "value": "Requires verification",
                "unit": "",
                "reference_range": "",
                "interpretation": "Requires verification"
            })

    return {
        "report_type": data.get("report_type") or fallback["report_type"],
        "source_confidence": data.get("source_confidence") or "medium",
        "extracted_tests": clean_tests[:30],
        "abnormal_findings": data.get("abnormal_findings") if isinstance(data.get("abnormal_findings"), list) else [],
        "clinical_summary": data.get("clinical_summary") or fallback["clinical_summary"],
        "faculty_verification_required": True
    }


def analyze_lab_report_text(text: str) -> Dict[str, Any]:
    cleaned = clean_lab_ocr(text)

    if not cleaned or len(cleaned) < 20:
        return deterministic_lab_fallback(text)

    prompt = f"""
You are a clinical laboratory report extraction assistant.

You will receive OCR text from a lab report image or PDF.

Tasks:
- Extract lab test names, values, units and reference ranges if readable.
- Identify abnormal findings only when values are clearly readable.
- Do not guess missing values.
- Do not expose patient name, hospital name, phone, address, UHID, registration number or doctor names.
- If OCR is unclear, write "Requires verification".

Return JSON only:

{{
  "report_type": "",
  "source_confidence": "high/medium/low",
  "extracted_tests": [
    {{
      "test_name": "",
      "value": "",
      "unit": "",
      "reference_range": "",
      "interpretation": ""
    }}
  ],
  "abnormal_findings": [],
  "clinical_summary": "",
  "faculty_verification_required": true
}}

OCR TEXT:
{cleaned[:8000]}
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
                    "num_predict": 1600
                }
            },
            timeout=120,
        )

        response.raise_for_status()
        raw = response.json().get("response", "")
        parsed = extract_json(raw)

        if not parsed:
            return deterministic_lab_fallback(text)

        return normalize_lab_analysis(parsed, text)

    except Exception:
        return deterministic_lab_fallback(text)
