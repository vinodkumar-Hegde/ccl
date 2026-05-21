import json
import ollama


SYSTEM_PROMPT = """
You are an expert clinical documentation analyzer.

Extract clinical progress notes from the case.

Return ONLY valid JSON.

Format:

{
  "clinical_notes": [
    {
      "day": "",
      "progress": "",
      "medication": "",
      "vitals": ""
    }
  ]
}

Rules:
- Generate meaningful structured notes from available case data.
- If exact timeline is unavailable, create logical progression.
- Keep content concise and medically relevant.
- Return empty array if nothing found.
"""


def generate_clinical_notes(text: str):
    try:
        response = ollama.chat(
            model="mistral",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": text[:12000]
                }
            ]
        )

        content = response["message"]["content"]

        start = content.find("{")
        end = content.rfind("}") + 1

        cleaned = content[start:end]

        return json.loads(cleaned)

    except Exception as e:
        return {
            "clinical_notes": [],
            "error": str(e)
        }