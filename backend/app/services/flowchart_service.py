import json
import ollama


SYSTEM_PROMPT = """
You are an expert medical clinical pathway generator.

Generate a structured treatment flowchart.

Return ONLY valid JSON.

Format:

{
  "flowchart": [
    {
      "step": "",
      "description": ""
    }
  ]
}

Rules:
- Create logical medical workflow.
- Use diagnosis, findings, treatment, and follow-up concepts.
- Keep descriptions concise.
- Minimum 4 steps.
"""


def generate_flowchart(text: str):
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
            "flowchart": [],
            "error": str(e)
        }