import json
import os
import re
import ollama


def _extract_json(text):
    match = re.search(r"\{[\s\S]*\}", text or "")
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def structure_clinical_summary(ai_summary: dict):
    prompt = f"""
Convert this clinical case summary into structured teaching format.

Return ONLY valid JSON:
{{
  "history": [
    {{"label": "Patient profile", "text": "..."}},
    {{"label": "Presenting complaint", "text": "..."}},
    {{"label": "Relevant background", "text": "..."}}
  ],
  "findings": [
    {{"label": "Examination", "text": "..."}},
    {{"label": "Investigations", "text": "..."}},
    {{"label": "Key abnormality", "text": "..."}}
  ],
  "significance": [
    {{"label": "Clinical meaning", "text": "..."}},
    {{"label": "Why it matters", "text": "..."}}
  ],
  "procedure_plan": [
    {{"label": "Immediate plan", "text": "..."}},
    {{"label": "Monitoring", "text": "..."}},
    {{"label": "Follow-up", "text": "..."}}
  ]
}}

Input:
{json.dumps(ai_summary, ensure_ascii=False)}
"""

    try:
        client = ollama.Client(
            host=os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
        )

        response = client.chat(
            model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            messages=[{"role": "user", "content": prompt}]
        )

        parsed = _extract_json(response["message"]["content"])

        if parsed:
            return parsed

    except Exception as e:
        print("Structured summary failed:", e)

    return {
        "history": [{"label": "Clinical context", "text": ai_summary.get("history", "Not clearly mentioned.")}],
        "findings": [{"label": "Clinical findings", "text": ai_summary.get("findings", "Not clearly mentioned.")}],
        "significance": [{"label": "Clinical significance", "text": ai_summary.get("significance", "Not clearly mentioned.")}],
        "procedure_plan": [{"label": "Planned procedure", "text": ai_summary.get("procedure_plan", "Not clearly mentioned.")}]
    }
