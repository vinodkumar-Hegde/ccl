import json
import os
import re

import ollama

from app.services.clinical_template_service import get_clinical_template_context


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")


SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "case_overview": {"type": "string"},
        "key_clinical_history": {"type": "string"},
        "examination_and_findings": {"type": "string"},
        "investigations": {"type": "string"},
        "diagnosis_or_impression": {"type": "string"},
        "management_plan": {"type": "string"},
        "teaching_points": {
            "type": "array",
            "items": {"type": "string"}
        },
        "extraction_quality": {"type": "string"},
        "unreadable_sections": {"type": "string"}
    },
    "required": [
        "case_overview",
        "key_clinical_history",
        "examination_and_findings",
        "investigations",
        "diagnosis_or_impression",
        "management_plan",
        "teaching_points",
        "extraction_quality",
        "unreadable_sections"
    ]
}


def _extract_json(text: str):
    match = re.search(r"\{[\s\S]*\}", text or "")
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def _fallback_summary(text: str):
    return {
        "case_overview": "The uploaded case sheet could not be reliably interpreted.",
        "key_clinical_history": "Not clearly readable in the uploaded case sheet.",
        "examination_and_findings": "Not clearly readable in the uploaded case sheet.",
        "investigations": "Not clearly readable in the uploaded case sheet.",
        "diagnosis_or_impression": "Not clearly readable in the uploaded case sheet.",
        "management_plan": "Not clearly readable in the uploaded case sheet.",
        "teaching_points": [
            "Image/document extraction quality must be improved before reliable academic interpretation."
        ],
        "extraction_quality": "Poor",
        "unreadable_sections": "Large portions of the case sheet were unclear or unreadable."
    }


def generate_medical_summary(
    extracted_text: str,
    department: str = "",
    speciality: str = ""
):
    if not extracted_text or len(extracted_text.strip()) < 50:
        return _fallback_summary(extracted_text)

    clinical_template = get_clinical_template_context(department, speciality)

    prompt = f"""
You are a senior clinician and medical educator.

You are given LLM vision-extracted content from a clinical case sheet PDF.

Your task:
Create a clinically useful academic case summary.

Safety rules:
1. Use only extracted content.
2. Do not invent facts.
3. Do not guess unreadable handwriting.
4. You may infer only common clinical grouping, not missing patient facts.
5. If unclear, write "Not clearly readable in the uploaded case sheet."
6. Keep summary useful for MBBS/PG students.
7. Return only JSON.

Clinical template:
{clinical_template}

Vision-extracted case sheet content:
{extracted_text[:12000]}
"""

    try:
        client = ollama.Client(host=OLLAMA_HOST)

        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            format=SUMMARY_SCHEMA,
            options={
                "temperature": 0
            }
        )

        parsed = _extract_json(response["message"]["content"])

        if not parsed:
            return _fallback_summary(extracted_text)

        final = _fallback_summary(extracted_text)

        for key in SUMMARY_SCHEMA["required"]:
            value = parsed.get(key)

            if key == "teaching_points":
                final[key] = value if isinstance(value, list) else final[key]
            elif isinstance(value, str) and value.strip():
                final[key] = value.strip()

        return final

    except Exception as error:
        print("Summary generation failed:", error)
        return _fallback_summary(extracted_text)
