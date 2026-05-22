import json
import os
import re

import ollama


def _extract_json_array(text: str):
    match = re.search(r"\[[\s\S]*\]", text or "")
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def generate_flowchart_from_summary(ai_summary: dict):
    history = ai_summary.get("history", "")
    findings = ai_summary.get("findings", "")
    significance = ai_summary.get("significance", "")
    procedure_plan = ai_summary.get("procedure_plan", "")
    conclusion = ai_summary.get("conclusion", "")
    clinical_notes = ai_summary.get("clinical_notes", [])

    prompt = f"""
You are a senior clinical education expert.

Create a clean clinical decision flowchart from this case.

Return ONLY valid JSON array.

Each item must be:
{{
  "step": "short step title",
  "description": "clear clinical explanation",
  "type": "start | assessment | investigation | decision | treatment | followup | outcome"
}}

Case History:
{history}

Findings:
{findings}

Clinical Significance:
{significance}

Planned Procedure:
{procedure_plan}

Clinical Notes:
{json.dumps(clinical_notes, ensure_ascii=False)}

Conclusion:
{conclusion}
"""

    try:
        client = ollama.Client(
            host=os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
        )

        response = client.chat(
            model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response["message"]["content"]
        parsed = _extract_json_array(content)

        if parsed:
            return parsed

    except Exception as error:
        print("LLM flowchart generation failed:", error)

    return [
        {
            "step": "Patient Presentation",
            "description": history or "Clinical presentation not clearly mentioned.",
            "type": "start"
        },
        {
            "step": "Clinical Assessment",
            "description": findings or "Clinical findings not clearly mentioned.",
            "type": "assessment"
        },
        {
            "step": "Clinical Significance",
            "description": significance or "Clinical significance not clearly mentioned.",
            "type": "decision"
        },
        {
            "step": "Planned Management",
            "description": procedure_plan or "Procedure plan not clearly mentioned.",
            "type": "treatment"
        },
        {
            "step": "Clinical Impression",
            "description": conclusion or "Conclusion not clearly mentioned.",
            "type": "outcome"
        }
    ]
