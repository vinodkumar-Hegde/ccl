import json
import requests
from typing import Any, Dict, List

OLLAMA_URL = "http://host.docker.internal:11434/api/generate"
RECONSTRUCTION_MODEL = "gemma2:9b"


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


def collect_lab_findings(case_files: List[Any]) -> List[Dict[str, Any]]:
    labs = []

    for file in case_files:
        if getattr(file, "file_type", None) != "lab_report":
            continue

        analysis = getattr(file, "ai_analysis", None)

        if not isinstance(analysis, dict):
            continue

        labs.append({
            "file_name": getattr(file, "original_name", None) or getattr(file, "filename", ""),
            "report_type": analysis.get("report_type", "Lab Report"),
            "source_confidence": analysis.get("source_confidence", "low"),
            "extracted_tests": analysis.get("extracted_tests", []),
            "abnormal_findings": analysis.get("abnormal_findings", []),
            "clinical_summary": analysis.get("clinical_summary", ""),
        })

    return labs


def high_yield_fallback(
    case_title: str,
    subject: str,
    speciality: str,
    disease: str,
    confirmed_summary: Dict[str, Any],
    lab_findings: List[Dict[str, Any]],
) -> Dict[str, Any]:
    topic = disease or case_title or speciality or subject or "Clinical Case"
    department = subject or "Clinical Medicine"
    speciality_name = speciality or department

    extracted = confirmed_summary or {}
    extracted_sections = extracted.get("structured_sections", {}) if isinstance(extracted, dict) else {}

    history_facts = extracted_sections.get("history_presenting_complaints", [])
    exam_facts = extracted_sections.get("clinical_examination_diagnostics", [])
    management_facts = extracted_sections.get("management_treatment_plan", [])

    lab_summary = []

    if lab_findings:
        for report in lab_findings:
            lab_summary.append(
                f"{report.get('report_type', 'Lab report')} was processed. Values should be reviewed before final interpretation."
            )

            for test in report.get("extracted_tests", [])[:10]:
                if isinstance(test, dict):
                    name = test.get("test_name", "Lab parameter")
                    value = test.get("value", "Not clearly readable")
                    unit = test.get("unit", "")
                    interpretation = test.get("interpretation", "")
                    lab_summary.append(f"{name}: {value} {unit}. {interpretation}".strip())
    else:
        lab_summary = [
            "Recommended baseline investigations include CBC, renal function tests, liver function tests, electrolytes, blood glucose, coagulation profile and blood grouping according to clinical context."
        ]

    return {
        "case_identity": {
            "case_type": extracted.get("case_type", "AI-Reconstructed Clinical Teaching Case"),
            "department": department,
            "speciality": speciality_name,
            "probable_topic": topic,
            "source_confidence": "AI-reconstructed from partial uploaded data",
            "faculty_verification_required": True,
        },
        "ai_reconstructed_teaching_case": {
            "case_title": f"High-Yield Clinical Teaching Case: {topic}",
            "patient_profile": (
                f"This is an AI-reconstructed educational case draft for {topic} under {speciality_name}. "
                "Patient identifiers are excluded. Demographic details should be added only if verified by faculty."
            ),
            "presenting_complaints": [
                f"Frame the chief complaint around the selected clinical topic: {topic}.",
                "Document onset, duration, progression, severity and associated symptoms.",
                "Include red-flag symptoms such as fever, vomiting, bleeding, breathlessness, altered sensorium, severe pain or rapid deterioration when relevant.",
                "Clarify whether the presentation was emergency, elective admission, referral, postoperative review or follow-up."
            ],
            "history_of_presenting_illness": (
                f"The reconstructed HPI for {topic} should describe symptom onset, duration, progression, associated symptoms, "
                "previous treatment, referral reason, current clinical status and impact on daily activity. "
                "This section is generated as an educational draft from partial source information."
            ),
            "past_history": [
                "Screen for diabetes, hypertension, CAD, asthma, tuberculosis, previous surgeries, previous admissions, blood transfusion history, drug allergies and long-term medication use.",
                "Identify comorbidities that affect diagnosis, anesthesia risk, operative planning, infection risk and recovery.",
                *[str(x) for x in history_facts[:4]]
            ],
            "personal_history": [
                "Document diet, appetite, bowel habits, micturition, sleep, occupation, tobacco/alcohol exposure and functional status.",
                "Assess lifestyle and risk factors relevant to the suspected diagnosis and perioperative/clinical risk."
            ],
            "family_history": [
                "Ask for family history of diabetes, hypertension, cardiac disease, stroke, malignancy, tuberculosis, asthma and inherited disorders.",
                "Mention family history only when it changes diagnostic probability or management."
            ],
            "general_examination": [
                "Record temperature, pulse, blood pressure, respiratory rate, oxygen saturation and general condition.",
                "Look for pallor, icterus, cyanosis, clubbing, lymphadenopathy, edema, dehydration and nutritional status.",
                "Assess pain, distress, hydration, sepsis indicators and hemodynamic stability.",
                *[str(x) for x in exam_facts[:4]]
            ],
            "systemic_examination": {
                "cardiovascular": [
                    "Assess heart sounds, rhythm, murmurs, peripheral perfusion and signs of cardiac failure where relevant."
                ],
                "respiratory": [
                    "Assess air entry, added sounds, respiratory distress and perioperative respiratory risk."
                ],
                "abdomen": [
                    "For surgical or abdominal cases, document inspection, palpation, tenderness, guarding, rigidity, organomegaly, bowel sounds and hernial sites where relevant."
                ],
                "cns": [
                    "Assess higher functions, motor/sensory status, reflexes and plantar response if neurological involvement is suspected."
                ]
            },
            "investigations": {
                "lab_interpretation": lab_summary,
                "imaging_interpretation": [
                    "Use disease-specific imaging such as X-ray, ultrasound, CT, MRI, endoscopy or procedure imaging according to clinical context.",
                    "Imaging findings should be treated as confirmed only after uploaded reports/images are reviewed."
                ],
                "other_tests": [
                    "Consider ECG, pre-anesthetic evaluation, culture/sensitivity, histopathology or disease-specific tests where relevant."
                ]
            },
            "probable_diagnosis": (
                f"Probable diagnosis should be finalized around the verified topic: {topic}. "
                "If source diagnosis is unreadable, keep diagnosis provisional until faculty review."
            ),
            "differential_diagnoses": [
                f"Generate differentials based on {topic}, anatomical site, symptom pattern and investigation findings.",
                "Include common, serious and easily missed alternatives.",
                "Separate provisional diagnosis from confirmed final diagnosis."
            ],
            "clinical_reasoning": (
                f"Clinical reasoning should connect presentation, risk factors, examination, labs and imaging to the probable {topic} diagnosis. "
                "A strong teaching case should explain why alternatives are less likely and what evidence confirms the final diagnosis."
            ),
            "management_plan": {
                "initial_management": [
                    "Assess airway, breathing, circulation, vitals, pain, hydration and sepsis risk.",
                    "Start supportive care according to clinical status: IV access, fluids, analgesia, antiemetics, oxygen or antibiotics when indicated."
                ],
                "medical_management": [
                    "Optimize comorbidities such as diabetes, hypertension, asthma, cardiac disease and infection risk.",
                    "Use disease-specific medical therapy only after diagnosis is verified."
                ],
                "surgical_or_procedure_plan": [
                    "Confirm diagnosis and indication for procedure.",
                    "Obtain consent, anesthesia evaluation, blood availability and preoperative optimization if surgery/procedure is planned.",
                    "Document operative findings, procedure performed, intraoperative complications and postoperative orders.",
                    *[str(x) for x in management_facts[:3]]
                ],
                "monitoring": [
                    "Monitor vitals, urine output, pain score, wound/procedure site, bleeding, infection markers and lab trends.",
                    "Escalate care if deterioration, sepsis, bleeding, respiratory distress, altered sensorium or oliguria develops."
                ],
                "discharge_advice": [
                    "Provide medication instructions, diet/activity advice, wound care, warning signs and follow-up schedule.",
                    "Advise urgent review for fever, worsening pain, bleeding, breathlessness, vomiting, altered sensorium or wound discharge."
                ]
            },
            "complications_to_watch": [
                "Disease progression or recurrence",
                "Infection or sepsis",
                "Bleeding",
                "Procedure-related complications",
                "Poor wound healing",
                "Comorbidity-related complications",
                "Delayed recovery or readmission"
            ],
            "red_flags": [
                "Hemodynamic instability",
                "Persistent high fever or sepsis features",
                "Severe or worsening pain",
                "Altered sensorium",
                "Respiratory distress",
                "Uncontrolled bleeding",
                "Reduced urine output",
                "Rapid clinical deterioration"
            ],
            "prognosis": (
                "Prognosis depends on verified diagnosis, severity, comorbidities, treatment timing, procedure findings, complications and response to therapy."
            ),
            "teaching_points": [],
            "student_questions": [],
            "faculty_notes": []
        },
        "extracted_source_facts": {
            "extracted_facts": confirmed_summary,
            "lab_reports": lab_findings
        },
        "missing_information_needed": [
            "Verified chief complaint and duration",
            "Verified history of presenting illness",
            "Verified examination findings",
            "Verified final diagnosis",
            "Verified lab values and reference ranges",
            "Verified imaging/procedure findings",
            "Verified treatment or operative notes",
            "Verified discharge advice"
        ],
        "safety_note": (
            "AI-reconstructed educational case draft based on partial uploaded data. "
            "Faculty review is required before publication."
        )
    }


def reconstruct_teaching_case(
    case_title: str,
    subject: str,
    speciality: str,
    disease: str,
    confirmed_summary: Dict[str, Any],
    case_files: List[Any],
) -> Dict[str, Any]:
    lab_findings = collect_lab_findings(case_files)

    # Always generate a high-yield educational reconstruction.
    # This avoids empty/weak LLM JSON responses being stored.
    return high_yield_fallback(
        case_title=case_title,
        subject=subject,
        speciality=speciality,
        disease=disease,
        confirmed_summary=confirmed_summary or {},
        lab_findings=lab_findings,
    )
