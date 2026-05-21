import ollama

MODEL_NAME = "mistral"


def generate_medical_summary(extracted_text: str):
    if not extracted_text or len(extracted_text.strip()) < 10:
        return empty_summary()

    prompt = f"""
You are a senior clinical case analyst.

The input is raw extracted text from a patient case sheet.
It may be unstructured, incomplete, handwritten OCR text, or without headings.

Your task:
Infer and organize the available clinical information into structured sections.

Return the answer in this exact format:

History:
Summarize patient demographics, chief complaints, duration, past history, relevant symptoms, and clinical background. Infer only from available text.

Findings:
Summarize examination findings, vitals, lab abnormalities, imaging findings, diagnosis clues, and important observations.

Significance:
Explain why this case is clinically important. Mention possible diagnosis, risk factors, severity, red flags, and learning value.

Procedure Plan:
Mention investigations, treatment plan, procedures, monitoring, medications, referrals, or follow-up suggested from the case. If not available, say "Not clearly mentioned".

Conclusion:
Give a concise clinical conclusion based on the available information.

Keywords:
Give 5 to 10 important medical keywords separated by commas.

Rules:
- Do not hallucinate.
- Do not invent patient details.
- If something is not available, write "Not mentioned".
- Use clinical language.
- Even if headings are absent, classify the text intelligently.

Raw case text:
{extracted_text[:5000]}
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0.2}
    )

    raw = response["message"]["content"]

    return {
        "history": extract_section(raw, "History", "Findings"),
        "findings": extract_section(raw, "Findings", "Significance"),
        "significance": extract_section(raw, "Significance", "Procedure Plan"),
        "procedure_plan": extract_section(raw, "Procedure Plan", "Conclusion"),
        "conclusion": extract_section(raw, "Conclusion", "Keywords"),
        "keywords": extract_keywords(raw)
    }


def extract_section(text, start, end):
    try:
        part = text.split(start + ":")[1]
        part = part.split(end + ":")[0]
        return part.strip() or "Not mentioned"
    except Exception:
        return "Not mentioned"


def extract_keywords(text):
    try:
        part = text.split("Keywords:")[1]
        return [
            item.strip()
            for item in part.replace("\n", ",").split(",")
            if item.strip()
        ]
    except Exception:
        return []


def empty_summary():
    return {
        "history": "No readable text found.",
        "findings": "Not mentioned",
        "significance": "Not mentioned",
        "procedure_plan": "Not clearly mentioned",
        "conclusion": "Not mentioned",
        "keywords": []
    }