import json
import os
import re
from pathlib import Path

import fitz
import ollama
from PIL import Image


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "llama3.2-vision:11b")


PAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "readability": {"type": "string"},
        "patient_identifiers_found": {"type": "string"},
        "visible_clinical_information": {"type": "string"},
        "complaints_history": {"type": "string"},
        "examination_findings": {"type": "string"},
        "investigations": {"type": "string"},
        "diagnosis_impression": {"type": "string"},
        "treatment_plan": {"type": "string"},
        "unclear_or_unreadable_parts": {"type": "string"}
    },
    "required": [
        "readability",
        "patient_identifiers_found",
        "visible_clinical_information",
        "complaints_history",
        "examination_findings",
        "investigations",
        "diagnosis_impression",
        "treatment_plan",
        "unclear_or_unreadable_parts"
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


def _render_pdf_pages(pdf_path: str, output_dir: str, max_pages: int = 8):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    image_paths = []

    for page_index in range(min(len(doc), max_pages)):
        page = doc[page_index]

        # 2x zoom improves handwriting/document readability
        matrix = fitz.Matrix(2.2, 2.2)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        img_path = Path(output_dir) / f"page_{page_index + 1}.png"
        pix.save(str(img_path))

        # optimize huge image lightly
        img = Image.open(img_path)
        img.thumbnail((1800, 2400))
        img.save(img_path)

        image_paths.append(str(img_path))

    return image_paths


def extract_pdf_with_vision(pdf_path: str, temp_dir: str = "storage/temp_vision"):
    image_paths = _render_pdf_pages(pdf_path, temp_dir)

    client = ollama.Client(host=OLLAMA_HOST)
    page_results = []

    for index, image_path in enumerate(image_paths, start=1):
        prompt = f"""
You are reading a clinical case sheet page as a medical document extraction assistant.

Extract only information visibly present on this page.

Very important rules:
1. Do not guess missing words.
2. Do not create diagnosis unless visible.
3. If handwriting is unclear, write "Not clearly readable".
4. Remove or avoid patient name, phone number, address, hospital name, doctor name if visible.
5. Keep medical abbreviations if visible.
6. Return only JSON.

This is page number {index}.
"""

        try:
            response = client.chat(
                model=VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [image_path]
                    }
                ],
                format=PAGE_SCHEMA,
                options={
                    "temperature": 0
                }
            )

            content = response["message"]["content"]
            parsed = _extract_json(content)

            if not parsed:
                parsed = {
                    "readability": "Unable to parse model output",
                    "patient_identifiers_found": "Unknown",
                    "visible_clinical_information": content[:2000],
                    "complaints_history": "Not clearly readable",
                    "examination_findings": "Not clearly readable",
                    "investigations": "Not clearly readable",
                    "diagnosis_impression": "Not clearly readable",
                    "treatment_plan": "Not clearly readable",
                    "unclear_or_unreadable_parts": "Model returned non-JSON output"
                }

            parsed["page_number"] = index
            page_results.append(parsed)

        except Exception as error:
            page_results.append(
                {
                    "page_number": index,
                    "readability": f"Vision extraction failed: {error}",
                    "patient_identifiers_found": "Unknown",
                    "visible_clinical_information": "Not extracted",
                    "complaints_history": "Not extracted",
                    "examination_findings": "Not extracted",
                    "investigations": "Not extracted",
                    "diagnosis_impression": "Not extracted",
                    "treatment_plan": "Not extracted",
                    "unclear_or_unreadable_parts": "Extraction failed"
                }
            )

    merged_text = []

    for page in page_results:
        merged_text.append(f"PAGE {page.get('page_number')}")
        merged_text.append(f"Readability: {page.get('readability')}")
        merged_text.append(f"Clinical Info: {page.get('visible_clinical_information')}")
        merged_text.append(f"Complaints/History: {page.get('complaints_history')}")
        merged_text.append(f"Examination: {page.get('examination_findings')}")
        merged_text.append(f"Investigations: {page.get('investigations')}")
        merged_text.append(f"Diagnosis/Impression: {page.get('diagnosis_impression')}")
        merged_text.append(f"Treatment Plan: {page.get('treatment_plan')}")
        merged_text.append(f"Unclear Parts: {page.get('unclear_or_unreadable_parts')}")
        merged_text.append("")

    return {
        "page_results": page_results,
        "merged_text": "\n".join(merged_text)
    }
