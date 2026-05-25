def get_clinical_template_context(department: str = "", speciality: str = ""):
    department = (department or "").lower()
    speciality = (speciality or "").lower()

    base = """
Use this clinical case framework:
- Case overview
- Key clinical history
- Examination and findings
- Investigations
- Diagnosis or clinical impression
- Management plan
- Teaching points

Use only extracted facts.
If data is unclear, say "Not clearly readable in the uploaded case sheet."
"""

    pediatric = """
For pediatric/neonatal cases, look for:
- age, sex
- birth weight
- gestational age
- mode of delivery
- respiratory support
- feeding status
- sepsis indicators
- NICU course
- discharge weight
- immunization or follow-up advice
"""

    cardiology = """
For cardiology cases, look for:
- chest pain, dyspnea, syncope, palpitations
- ECG findings
- troponin/enzymes
- echo findings
- angiography/PCI/CABG plan
- medications and risk factors
"""

    obg = """
For obstetrics and gynecology cases, look for:
- gravida/para status
- gestational age
- antenatal risk factors
- delivery details
- maternal and fetal status
- postpartum advice
"""

    medicine = """
For medicine cases, look for:
- presenting complaints
- duration and timeline
- comorbidities
- vitals and systemic examination
- lab/imaging abnormalities
- final diagnosis
- treatment and follow-up plan
"""

    context = base

    if "pedia" in department or "neonat" in speciality:
        context += pediatric

    if "cardio" in department or "cardio" in speciality:
        context += cardiology

    if "obg" in department or "gyn" in department or "obst" in speciality:
        context += obg

    if "medicine" in department or "medical" in department:
        context += medicine

    return context
