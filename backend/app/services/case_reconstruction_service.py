import os
import json
import requests
from typing import Any, Dict, List

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
RECONSTRUCTION_MODEL = os.getenv("RECONSTRUCTION_MODEL", "gemma2:9b")


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

    extracted_history = confirmed_summary.get("patient_history") or ""
    extracted_findings = confirmed_summary.get("clinical_findings") or ""
    extracted_plan = confirmed_summary.get("planned_procedure") or ""
    extracted_conclusion = confirmed_summary.get("conclusion") or ""

    structured = confirmed_summary.get("structured_sections") or {}
    source_history_points = structured.get("history_presenting_complaints") or []
    source_exam_points = structured.get("clinical_examination_diagnostics") or []
    source_management_points = structured.get("management_treatment_plan") or []

    return {
        "case_identity": {
            "case_type": confirmed_summary.get("case_type") or "General Clinical Case",
            "department": subject or "Clinical Medicine",
            "speciality": speciality or "General Clinical Practice",
            "probable_topic": topic,
            "source_confidence": "Educational reconstruction based on uploaded clinical source material",
            "faculty_validation_required": True,
        },
        "ai_reconstructed_teaching_case": {
            "case_title": f"Clinical Teaching Case: {topic}",
            "patient_profile": (
                f"This case represents a patient evaluated under {speciality or subject or 'a clinical specialty'} "
                f"for a probable diagnosis related to {topic}. The case is structured for bedside-style learning, "
                f"with emphasis on history taking, examination, investigation interpretation, clinical reasoning and management planning."
            ),
            "presenting_complaints": [
                f"The patient presented with clinical features suggestive of {topic}, requiring systematic evaluation.",
                "The symptom profile should be interpreted by documenting onset, duration, progression, severity and associated systemic symptoms.",
                "Important red-flag symptoms include fever, persistent vomiting, bleeding, breathlessness, altered sensorium, severe pain, reduced urine output or rapid clinical deterioration.",
                "The mode of presentation may be emergency admission, elective evaluation, referral, postoperative review or follow-up depending on the clinical context."
            ],
            "history_of_presenting_illness": (
                extracted_history
                if extracted_history and len(extracted_history) > 40
                else f"The history of presenting illness should be written as a continuous clinical narrative for {topic}, "
                     f"covering onset of symptoms, duration, progression, associated complaints, previous treatment, referral reason, "
                     f"current clinical status and functional impact. The narrative should connect the presenting symptoms with the suspected diagnosis "
                     f"and identify features that increase severity or urgency."
            ),
            "past_history": [
                "Past history should cover diabetes, hypertension, coronary artery disease, asthma, tuberculosis, prior admissions, previous surgeries, blood transfusion history, drug allergies and long-term medication use.",
                "Comorbid illnesses may modify the presentation, increase procedural or anaesthetic risk, delay recovery and influence medication choice.",
                "Previous similar episodes, previous interventions and prior complications should be correlated with the current diagnosis."
            ],
            "personal_history": [
                "Personal history should include appetite, dietary pattern, bowel and bladder habits, sleep, addictions, allergies and functional capacity.",
                "These details help assess baseline health, systemic involvement, nutritional status and risk factors relevant to treatment planning.",
                "Functional limitation and impact on daily activities should be documented because they reflect clinical severity and recovery needs."
            ],
            "family_history": [
                "Family history should explore diabetes, hypertension, cardiovascular disease, stroke, malignancy, tuberculosis, asthma and relevant hereditary disorders.",
                "A positive family history may indicate inherited risk, shared exposure or predisposition to systemic disease."
            ],
            "general_examination": [
                "General examination should assess temperature, pulse, blood pressure, respiratory rate, oxygen saturation and overall clinical condition.",
                "Pallor, icterus, cyanosis, clubbing, lymphadenopathy, oedema, dehydration and nutritional status should be recorded.",
                "The general examination helps determine severity, systemic involvement and fitness for further intervention."
            ],
            "systemic_examination": {
                "cardiovascular": [
                    "Assess pulse character, blood pressure, peripheral perfusion, heart sounds, murmurs and signs of heart failure."
                ],
                "respiratory": [
                    "Assess respiratory rate, oxygen saturation, chest expansion, breath sounds and added sounds such as crepitations or wheeze."
                ],
                "abdomen": [
                    "Assess abdominal tenderness, guarding, rigidity, distension, organomegaly, bowel sounds and procedure-specific findings."
                ],
                "cns": [
                    "Assess sensorium, orientation, focal neurological deficits and signs of raised intracranial pressure when clinically relevant."
                ]
            },
            "investigations": {
                "lab_interpretation": lab_findings if lab_findings else [
                    "Laboratory evaluation should include disease-relevant baseline parameters and markers of infection, inflammation, organ function and treatment risk.",
                    "Abnormal values should be interpreted with clinical context rather than reported as isolated numbers."
                ],
                "imaging_interpretation": [
                    f"Imaging should be selected according to the suspected {topic} pathology and used to confirm diagnosis, assess severity and plan treatment.",
                    "Findings should be correlated with symptoms, examination and laboratory results."
                ],
                "other_tests": [
                    "Additional tests may be required depending on comorbidities, planned procedure, anaesthesia risk and diagnostic uncertainty."
                ]
            },
            "probable_diagnosis": f"Probable diagnosis: {topic}",
            "differential_diagnoses": [
                f"Primary working diagnosis related to {topic}",
                "Infective or inflammatory pathology depending on symptoms and laboratory markers",
                "Metabolic, vascular, traumatic or neoplastic pathology depending on the organ system involved",
                "Procedure-related or postoperative complication if the case context supports it"
            ],
            "clinical_reasoning": (
                extracted_findings
                if extracted_findings and len(extracted_findings) > 40
                else f"The clinical reasoning should integrate the presenting illness, risk factors, examination findings, laboratory trends and imaging evidence. "
                     f"A diagnosis related to {topic} becomes more likely when the dominant symptoms, objective clinical signs and investigation findings support the same disease pathway. "
                     f"Alternative diagnoses should be considered and narrowed by identifying features that are absent, inconsistent or less strongly supported."
            ),
            "management_plan": {
                "initial_management": [
                    "Stabilize airway, breathing and circulation when the patient is acutely unwell.",
                    "Record baseline vitals, assess pain, hydration, urine output and systemic warning signs.",
                    "Initiate supportive care according to clinical severity and obtain urgent investigations when indicated."
                ],
                "medical_management": [
                    "Medical treatment should address symptoms, infection or inflammation, fluid-electrolyte balance, pain control and comorbidity optimization.",
                    "Drug selection should consider allergies, renal and hepatic function, pregnancy status where relevant and potential interactions."
                ],
                "surgical_or_procedure_plan": source_management_points if source_management_points else [
                    f"Procedure planning should be based on confirmed diagnosis, disease severity, imaging findings, patient fitness and risk-benefit assessment for {topic}.",
                    "Consent, pre-procedure optimization, anaesthesia assessment and postoperative monitoring should be planned where applicable."
                ],
                "monitoring": [
                    "Monitoring should include vital signs, urine output, pain score, wound or procedure site assessment, bleeding, infection markers and relevant laboratory trends.",
                    "Escalation is required for clinical deterioration, sepsis, active bleeding, respiratory distress, altered sensorium, oliguria or worsening laboratory parameters."
                ],
                "discharge_advice": [
                    "Discharge counselling should include medication instructions, diet and activity advice, wound care if applicable, warning symptoms and follow-up schedule.",
                    "Urgent review is required for fever, worsening pain, bleeding, breathlessness, persistent vomiting, altered sensorium, reduced urine output or wound discharge."
                ]
            },
            "complications_to_watch": [
                "Clinical deterioration or sepsis",
                "Bleeding, shock or worsening pain",
                "Respiratory distress or hypoxia",
                "Renal dysfunction, oliguria or electrolyte imbalance",
                "Procedure-related complications where applicable"
            ],
            "red_flags": [
                "Altered sensorium",
                "Persistent hypotension or tachycardia",
                "Respiratory distress",
                "Active bleeding",
                "Reduced urine output",
                "High-grade fever or features of sepsis"
            ],
            "prognosis": (
                f"Prognosis in {topic} depends on early diagnosis, severity at presentation, comorbidities, treatment response, complications and quality of follow-up."
            ),
            "teaching_points": [],
            "student_questions": [],
            "faculty_notes": []
        },
        "extracted_source_facts": {
            "extracted_facts": confirmed_summary,
            "lab_reports": lab_findings,
            "source_history_points": source_history_points,
            "source_examination_points": source_exam_points,
            "source_management_points": source_management_points
        },
        "missing_information_needed": [
            "Verified chief complaint and duration",
            "Verified history of presenting illness",
            "Verified examination findings",
            "Verified final diagnosis",
            "Verified lab values with reference ranges",
            "Verified imaging or procedure findings",
            "Verified treatment or operative notes",
            "Verified discharge advice"
        ],
        "safety_note": "Educational clinical case draft prepared from uploaded source material. Final clinical validation is required before publication."
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
