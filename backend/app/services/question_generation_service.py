import os
import json
import ollama

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")

client = ollama.Client(host=OLLAMA_HOST)

PROMPT = """
You are a senior medical educator.

Generate clinical educational questions from the given clinical case.

Return STRICT JSON format:

{
  "questions": [
    {
      "type": "Viva",
      "question": "..."
    },
    {
      "type": "MCQ",
      "question": "..."
    }
  ]
}

Generate:
- Viva questions
- Clinical reasoning questions
- Investigation questions
- Management questions
- Differential diagnosis questions

Keep questions concise and clinically meaningful.

Clinical Case:
"""

def generate_case_questions(text: str):
    try:
        response = client.chat(
            model="llama3.1:8b",
            messages=[
                {
                    "role": "user",
                    "content": PROMPT + text
                }
            ]
        )

        content = response["message"]["content"]

        start = content.find("{")
        end = content.rfind("}") + 1

        cleaned = content[start:end]

        data = json.loads(cleaned)

        return data.get("questions", [])

    except Exception as e:
        print("QUESTION GENERATION ERROR:", e)

        return []
