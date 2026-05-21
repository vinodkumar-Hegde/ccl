import json
import ollama


SYSTEM_PROMPT = """
You are an expert medical laboratory report analyzer.

Extract structured laboratory findings from the given report.

Return ONLY valid JSON.

Format:

{
  "tests": [
    {
      "test_name": "",
      "value": "",
      "normal_range": "",
      "status": "",
      "interpretation": ""
    }
  ]
}

Rules:
- status must be one of:
  Normal
  High
  Low
  Critical

- interpretation should be short and medically meaningful.
- Ignore unrelated text.
- Return empty tests array if nothing found.
"""


def analyze_lab_report(text: str):
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
            "tests": [],
            "error": str(e)
        }