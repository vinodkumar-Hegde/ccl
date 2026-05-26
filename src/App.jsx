import { useEffect, useMemo, useState } from "react";
import { Routes, Route, useNavigate, useParams } from "react-router-dom";
import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8001",
});

function parseAI(value) {
  if (!value) return {};
  if (typeof value === "object") return value;
  try {
    return JSON.parse(value);
  } catch {
    return {};
  }
}


function stringifyBlock(value) {
  if (!value) return "";

  if (typeof value === "string") return value;

  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === "string") return item;
        return JSON.stringify(item, null, 2);
      })
      .join("\n");
  }

  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}


function getReconstructedCase(aiSummary) {
  const root = parseAI(aiSummary);
  const reconstructed = root.ai_reconstructed_case || {};
  const teaching = reconstructed.ai_reconstructed_teaching_case || {};

  return {
    reconstructed,
    teaching,
    extractedFacts: root.extracted_facts || {},
  };
}

function listToText(value) {
  if (!value) return "";

  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === "string") return item;
        return JSON.stringify(item, null, 2);
      })
      .join("\n");
  }

  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}

function textToList(value) {
  return String(value || "")
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function getReconstructedForm(aiSummary) {
  const { reconstructed, teaching } = getReconstructedCase(aiSummary);

  return {
    case_title: teaching.case_title || "",
    patient_profile: teaching.patient_profile || "",
    presenting_complaints: listToText(teaching.presenting_complaints),
    history_of_presenting_illness: teaching.history_of_presenting_illness || "",
    past_history: listToText(teaching.past_history),
    personal_history: listToText(teaching.personal_history),
    family_history: listToText(teaching.family_history),
    general_examination: listToText(teaching.general_examination),
    systemic_examination: listToText(teaching.systemic_examination),
    investigations: listToText(teaching.investigations),
    probable_diagnosis: teaching.probable_diagnosis || "",
    differential_diagnoses: listToText(teaching.differential_diagnoses),
    clinical_reasoning: teaching.clinical_reasoning || "",
    management_plan: listToText(teaching.management_plan),
    complications_to_watch: listToText(teaching.complications_to_watch),
    red_flags: listToText(teaching.red_flags),
    prognosis: teaching.prognosis || "",
    missing_information_needed: listToText(reconstructed.missing_information_needed),
    safety_note: reconstructed.safety_note || "",
  };
}

function buildReconstructedSummary(existingAiSummary, form) {
  const root = parseAI(existingAiSummary);
  const reconstructed = root.ai_reconstructed_case || {};
  const teaching = reconstructed.ai_reconstructed_teaching_case || {};

  let systemic = {};
  let investigations = {};
  let management = {};

  try {
    systemic = form.systemic_examination ? JSON.parse(form.systemic_examination) : {};
  } catch {
    systemic = { notes: textToList(form.systemic_examination) };
  }

  try {
    investigations = form.investigations ? JSON.parse(form.investigations) : {};
  } catch {
    investigations = { notes: textToList(form.investigations) };
  }

  try {
    management = form.management_plan ? JSON.parse(form.management_plan) : {};
  } catch {
    management = { notes: textToList(form.management_plan) };
  }

  return {
    ...root,
    ai_reconstructed_case: {
      ...reconstructed,
      ai_reconstructed_teaching_case: {
        ...teaching,
        case_title: form.case_title,
        patient_profile: form.patient_profile,
        presenting_complaints: textToList(form.presenting_complaints),
        history_of_presenting_illness: form.history_of_presenting_illness,
        past_history: textToList(form.past_history),
        personal_history: textToList(form.personal_history),
        family_history: textToList(form.family_history),
        general_examination: textToList(form.general_examination),
        systemic_examination: systemic,
        investigations: investigations,
        probable_diagnosis: form.probable_diagnosis,
        differential_diagnoses: textToList(form.differential_diagnoses),
        clinical_reasoning: form.clinical_reasoning,
        management_plan: management,
        complications_to_watch: textToList(form.complications_to_watch),
        red_flags: textToList(form.red_flags),
        prognosis: form.prognosis,
        teaching_points: [],
        student_questions: [],
        faculty_notes: [],
      },
      missing_information_needed: textToList(form.missing_information_needed),
      safety_note: form.safety_note,
    },
  };
}


function getAdminFormFromAI(aiSummary) {
  const root = parseAI(aiSummary);

  const extracted = root.extracted_facts || root || {};
  const reconstructed = root.ai_reconstructed_case || {};
  const teaching = reconstructed.ai_reconstructed_teaching_case || {};
  const structured = extracted.structured_sections || {};

  const managementPlan = teaching.management_plan || {};

  return {
    patient_history:
      teaching.history_of_presenting_illness ||
      extracted.patient_history ||
      "",

    clinical_findings:
      teaching.clinical_reasoning ||
      extracted.clinical_findings ||
      "",

    clinical_significance:
      extracted.clinical_significance ||
      reconstructed.safety_note ||
      "",

    planned_procedure:
      stringifyBlock(managementPlan) ||
      extracted.planned_procedure ||
      "",

    conclusion:
      extracted.conclusion ||
      reconstructed.safety_note ||
      "",

    history_presenting_complaints:
      listToTextarea(
        structured.history_presenting_complaints ||
          teaching.presenting_complaints ||
          teaching.past_history ||
          []
      ),

    clinical_examination_diagnostics:
      listToTextarea(
        structured.clinical_examination_diagnostics ||
          teaching.general_examination ||
          []
      ),

    management_treatment_plan:
      listToTextarea(
        structured.management_treatment_plan ||
          managementPlan.surgical_or_procedure_plan ||
          managementPlan.medical_management ||
          []
      ),
  };
}


function toText(item) {
  if (!item) return "";
  if (typeof item === "string") return item;

  if (typeof item === "object") {
    return Object.entries(item)
      .map(([key, value]) => {
        if (typeof value === "object") {
          return `${key}: ${JSON.stringify(value)}`;
        }
        return `${key}: ${value}`;
      })
      .join(" | ");
  }

  return String(item);
}

function cleanList(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value.map(toText).filter(Boolean);
  return [toText(value)].filter(Boolean);
}

function listToTextarea(value) {
  return cleanList(value).join("\n");
}

function textareaToList(value) {
  return String(value || "")
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function Section({ title, children }) {
  return (
    <section className="caseDetailSection smartClinicalCard">
      <h2>{title}</h2>
      <div className="caseDetailContent clinicalCardBody">{children}</div>
    </section>
  );
}

function BulletList({ items }) {
  const list = cleanList(items);

  if (!list.length) {
    return <p>Not clearly documented.</p>;
  }

  return (
    <ul className="clinicalBulletList">
      {list.map((item, index) => (
        <li key={index}>{item}</li>
      ))}
    </ul>
  );
}

function LibraryPage({ navigateToCase }) {
  const [cases, setCases] = useState([]);
  const [search, setSearch] = useState("");
  const [subject, setSubject] = useState("");
  const [speciality, setSpeciality] = useState("");
  const [disease, setDisease] = useState("");

  async function loadCases() {
    try {
      const response = await api.get(`/cases/published?t=${Date.now()}`);
      setCases(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error("Failed to load published cases", error);
    }
  }

  useEffect(() => {
    loadCases();
  }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();

    if (!q) return cases;

    return cases.filter((item) => {
      const ai = parseAI(item.ai_summary);
      const text = [
        item.case_title,
        item.subject,
        item.speciality,
        item.super_speciality,
        item.disease,
        ai.patient_history,
        ai.clinical_findings,
        JSON.stringify(ai.structured_sections || {}),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return text.includes(q);
    });
  }, [cases, search]);

  const subjects = [...new Set(filtered.map((c) => c.subject).filter(Boolean))];

  const specialities = subject
    ? [
        ...new Set(
          filtered
            .filter((c) => c.subject === subject)
            .map((c) => c.super_speciality || c.speciality)
            .filter(Boolean)
        ),
      ]
    : [];

  const diseases =
    subject && speciality
      ? [
          ...new Set(
            filtered
              .filter(
                (c) =>
                  c.subject === subject &&
                  (c.super_speciality || c.speciality) === speciality
              )
              .map((c) => c.disease)
              .filter(Boolean)
          ),
        ]
      : [];

  const visibleCases =
    subject && speciality && disease
      ? filtered.filter(
          (c) =>
            c.subject === subject &&
            (c.super_speciality || c.speciality) === speciality &&
            c.disease === disease
        )
      : [];

  return (
    <div className="libraryPage">
      <header className="libraryHero">
        <div className="libraryLogoBox">
          <img src="/logo.png" alt="DocTutorials" />
        </div>

        <div>
          <h1>Clinical Case Library</h1>
          <p>Explore cases by Subject → Super Speciality → Disease → Case.</p>
        </div>

        <button className="refreshBtn" onClick={loadCases}>
          Refresh
        </button>
      </header>

      <div className="librarySearchBox">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search case by title, subject, speciality, disease..."
        />
      </div>

      <section
        className={
          subject
            ? "dynamicLibraryFlow activeFlow"
            : "dynamicLibraryFlow initialSubjectFlow"
        }
      >
        <div className="flowColumn subjectColumn">
          <h2>Subjects</h2>

          {subjects.length === 0 ? (
            <div className="emptyLibraryState">No published subjects found.</div>
          ) : (
            subjects.map((item) => (
              <button
                key={item}
                type="button"
                className={subject === item ? "libraryNode active" : "libraryNode"}
                onClick={() => {
                  setSubject(subject === item ? "" : item);
                  setSpeciality("");
                  setDisease("");
                }}
              >
                <span className="libraryIcon">🧪</span>
                <div>
                  <strong>{item}</strong>
                  <span>Medical Subject</span>
                </div>
              </button>
            ))
          )}
        </div>

        {subject && (
          <div className="flowColumn">
            <h2>Super Specialities</h2>

            {specialities.map((item) => (
              <button
                key={item}
                type="button"
                className={speciality === item ? "libraryNode active" : "libraryNode"}
                onClick={() => {
                  setSpeciality(speciality === item ? "" : item);
                  setDisease("");
                }}
              >
                <span className="libraryIcon">🩺</span>
                <div>
                  <strong>{item}</strong>
                  <span>Super Speciality</span>
                </div>
              </button>
            ))}
          </div>
        )}

        {speciality && (
          <div className="flowColumn">
            <h2>Diseases</h2>

            {diseases.map((item) => (
              <button
                key={item}
                type="button"
                className={disease === item ? "libraryNode active" : "libraryNode"}
                onClick={() => setDisease(disease === item ? "" : item)}
              >
                <span className="libraryIcon">🧠</span>
                <div>
                  <strong>{item}</strong>
                  <span>Disease Category</span>
                </div>
              </button>
            ))}
          </div>
        )}

        {disease && (
          <div className="flowColumn">
            <h2>Cases</h2>

            {visibleCases.map((item) => (
              <button
                key={item.id}
                type="button"
                className="libraryCaseCard"
                onClick={() => navigateToCase(item.id)}
              >
                <span className="libraryIcon">🧾</span>
                <div>
                  <strong>{item.case_title}</strong>
                  <span>Clinical Case</span>
                </div>
                <small>Case #{item.id}</small>
              </button>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function UploadCase() {
  const [form, setForm] = useState({
    subject: "",
    speciality: "",
    disease: "",
    case_title: "",
  });

  const [caseSheet, setCaseSheet] = useState(null);
  const [labReports, setLabReports] = useState([]);
  const [images, setImages] = useState([]);
  const [videos, setVideos] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  function update(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function submit(e) {
    e.preventDefault();

    if (!caseSheet) {
      alert("Please upload case sheet");
      return;
    }

    setUploading(true);
    setMessage("");

    try {
      const data = new FormData();

      data.append("subject", form.subject);
      data.append("speciality", form.speciality);
      data.append("disease", form.disease);
      data.append("case_title", form.case_title);
      data.append("case_sheet", caseSheet);

      labReports.forEach((file) => data.append("lab_reports", file));
      images.forEach((file) => data.append("images", file));
      videos.forEach((file) => data.append("videos", file));

      const response = await api.post("/full-process/case", data, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setMessage(
        `Uploaded successfully. Case ID: ${response.data.case_id}. AI processing started.`
      );
    } catch (error) {
      const detail = error?.response?.data?.detail || error.message;
      setMessage(`Upload failed: ${detail}`);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="adminCard">
      <h1>Upload Clinical Case</h1>

      <form onSubmit={submit} className="adminForm">
        <input
          name="subject"
          placeholder="Subject"
          value={form.subject}
          onChange={update}
          required
        />

        <input
          name="speciality"
          placeholder="Super Speciality"
          value={form.speciality}
          onChange={update}
          required
        />

        <input
          name="disease"
          placeholder="Disease"
          value={form.disease}
          onChange={update}
          required
        />

        <input
          name="case_title"
          placeholder="Case Title"
          value={form.case_title}
          onChange={update}
          required
        />

        <label>Case Sheet / Discharge Summary</label>
        <input
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={(e) => setCaseSheet(e.target.files[0])}
          required
        />

        <label>Lab Reports</label>
        <input
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          multiple
          onChange={(e) => setLabReports(Array.from(e.target.files))}
        />

        <label>Clinical Images</label>
        <input
          type="file"
          accept=".jpg,.jpeg,.png"
          multiple
          onChange={(e) => setImages(Array.from(e.target.files))}
        />

        <label>Clinical Videos</label>
        <input
          type="file"
          accept=".mp4,.mov,.avi"
          multiple
          onChange={(e) => setVideos(Array.from(e.target.files))}
        />

        <button type="submit" disabled={uploading}>
          {uploading ? "Uploading..." : "Upload + Start AI Processing"}
        </button>
      </form>

      {message && <div className="uploadStatusBox">{message}</div>}
    </div>
  );
}

function ManageUploads({ openEdit }) {
  const [cases, setCases] = useState([]);
  const [search, setSearch] = useState("");

  async function loadCases() {
    try {
      const response = await api.get(`/cases/?t=${Date.now()}`);
      setCases(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error("Failed to fetch cases", error);
    }
  }

  useEffect(() => {
    loadCases();
  }, []);

  const filtered = cases.filter((item) =>
    [
      item.id,
      item.case_title,
      item.subject,
      item.speciality,
      item.disease,
      item.status,
      item.processing_status,
    ]
      .join(" ")
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <div className="adminCard">
      <div className="dashboardTop">
        <div>
          <h1>Uploads Dashboard</h1>
          <p>Search, filter, edit and publish uploaded clinical cases.</p>
        </div>

        <button className="modernRefreshBtn" onClick={loadCases}>
          Refresh
        </button>
      </div>

      <div className="modernSearchBar">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by ID, title, subject, speciality, disease..."
        />
      </div>

      <div className="tableWrap">
        <table className="adminTable modernTable">
          <thead>
            <tr>
              <th>ID</th>
              <th>Case Title</th>
              <th>Subject</th>
              <th>Speciality</th>
              <th>Disease</th>
              <th>Publish Status</th>
              <th>AI Status</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {filtered.map((item) => (
              <tr key={item.id}>
                <td>#{item.id}</td>
                <td>
                  <strong>{item.case_title}</strong>
                </td>
                <td>{item.subject}</td>
                <td>{item.speciality}</td>
                <td>{item.disease}</td>
                <td>{item.status}</td>
                <td>{item.processing_status}</td>
                <td>
                  <button
                    className="modernEditBtn"
                    onClick={() => openEdit(item.id)}
                  >
                    Edit
                  </button>
                </td>
              </tr>
            ))}

            {!filtered.length && (
              <tr>
                <td colSpan="8" className="emptyTable">
                  No cases found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function EditPublish({ selectedCaseId }) {
  const [cases, setCases] = useState([]);
  const [selectedId, setSelectedId] = useState(selectedCaseId || "");
  const [selectedCase, setSelectedCase] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const [form, setForm] = useState({
    case_title: "",
    patient_profile: "",
    presenting_complaints: "",
    history_of_presenting_illness: "",
    past_history: "",
    personal_history: "",
    family_history: "",
    general_examination: "",
    systemic_examination: "",
    investigations: "",
    probable_diagnosis: "",
    differential_diagnoses: "",
    clinical_reasoning: "",
    management_plan: "",
    complications_to_watch: "",
    red_flags: "",
    prognosis: "",
    missing_information_needed: "",
    safety_note: "",
  });

  async function loadCases() {
    const response = await api.get(`/cases/?t=${Date.now()}`);
    const list = Array.isArray(response.data) ? response.data : [];
    setCases(list);

    if (selectedCaseId) {
      loadCase(selectedCaseId);
    } else if (list.length && !selectedCase) {
      loadCase(list[0].id);
    }
  }

  async function loadCase(id) {
    const response = await api.get(`/cases/${id}?t=${Date.now()}`);
    const data = response.data;
    const ai = parseAI(data.ai_summary);
    const structured = ai.structured_sections || {};

    setSelectedId(String(id));
    setSelectedCase(data);

    setForm(getReconstructedForm(data.ai_summary));

    setMessage("");
  }

  useEffect(() => {
    loadCases();
  }, [selectedCaseId]);

  function updateField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function save(statusValue = null) {
    if (!selectedCase) return;

    setSaving(true);
    setMessage("");

    const ai_summary = buildReconstructedSummary(selectedCase.ai_summary, form);

    try {
      await api.put(`/case-ai/${selectedCase.id}`, {
        case_title: selectedCase.case_title,
        subject: selectedCase.subject,
        speciality: selectedCase.speciality,
        disease: selectedCase.disease,
        status: statusValue || selectedCase.status || "draft",
        ai_summary,
      });

      if (statusValue === "published") {
        try {
          await api.put(`/cases/${selectedCase.id}/publish`);
        } catch {
          console.warn("Publish route failed; status sent through case-ai.");
        }
      }

      setMessage(statusValue === "published" ? "Published successfully." : "Saved successfully.");
      await loadCase(selectedCase.id);
      await loadCases();
    } catch (error) {
      console.error("Save failed", error);
      setMessage("Save failed. Check backend logs.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="editPublishPage">
      <h1>Edit & Publish Case</h1>

      <div className="editTopBar">
        <label>Select Case</label>
        <select value={selectedId} onChange={(e) => loadCase(e.target.value)}>
          {cases.map((item) => (
            <option key={item.id} value={item.id}>
              {item.case_title || `Case ${item.id}`} | ID: {item.id}
            </option>
          ))}
        </select>
      </div>

      {selectedCase && (
        <p className="editCaseMeta">
          <strong>{selectedCase.case_title}</strong> | Case ID: {selectedCase.id} |
          Status: {selectedCase.status || "draft"} | Processing:{" "}
          {selectedCase.processing_status || "unknown"}
        </p>
      )}

      <div className="reconstructionHeader">
        <h2>AI Reconstructed Teaching Case</h2>
        <p>
          This is an AI-generated educational case draft from partial uploaded data.
          Review, edit and publish only after verification.
        </p>
      </div>

      <div className="editGrid reconstructionGrid">
        <div className="editCard fullWidthClinicalCard priorityClinicalCard">
          <label>Case Title</label>
          <textarea
            value={form.case_title}
            onChange={(e) => updateField("case_title", e.target.value)}
            placeholder="Case title"
          />
        </div>

        <div className="editCard fullWidthClinicalCard">
          <label>Patient Profile</label>
          <textarea
            value={form.patient_profile}
            onChange={(e) => updateField("patient_profile", e.target.value)}
            placeholder="AI reconstructed patient profile"
          />
        </div>

        <div className="editCard fullWidthClinicalCard">
          <label>Presenting Complaints</label>
          <textarea
            value={form.presenting_complaints}
            onChange={(e) => updateField("presenting_complaints", e.target.value)}
            placeholder="One point per line"
          />
        </div>

        <div className="editCard fullWidthClinicalCard">
          <label>History of Presenting Illness</label>
          <textarea
            value={form.history_of_presenting_illness}
            onChange={(e) => updateField("history_of_presenting_illness", e.target.value)}
            placeholder="Detailed HPI"
          />
        </div>

        <div className="editCard">
          <label>Past History</label>
          <textarea
            value={form.past_history}
            onChange={(e) => updateField("past_history", e.target.value)}
            placeholder="One point per line"
          />
        </div>

        <div className="editCard">
          <label>Personal History</label>
          <textarea
            value={form.personal_history}
            onChange={(e) => updateField("personal_history", e.target.value)}
            placeholder="One point per line"
          />
        </div>

        <div className="editCard">
          <label>Family History</label>
          <textarea
            value={form.family_history}
            onChange={(e) => updateField("family_history", e.target.value)}
            placeholder="One point per line"
          />
        </div>

        <div className="editCard">
          <label>General Examination</label>
          <textarea
            value={form.general_examination}
            onChange={(e) => updateField("general_examination", e.target.value)}
            placeholder="One point per line"
          />
        </div>

        <div className="editCard fullWidthClinicalCard">
          <label>Systemic Examination JSON</label>
          <textarea
            value={form.systemic_examination}
            onChange={(e) => updateField("systemic_examination", e.target.value)}
            placeholder="Systemic examination JSON"
          />
        </div>

        <div className="editCard fullWidthClinicalCard">
          <label>Investigations JSON</label>
          <textarea
            value={form.investigations}
            onChange={(e) => updateField("investigations", e.target.value)}
            placeholder="Investigations JSON"
          />
        </div>

        <div className="editCard">
          <label>Probable Diagnosis</label>
          <textarea
            value={form.probable_diagnosis}
            onChange={(e) => updateField("probable_diagnosis", e.target.value)}
            placeholder="Probable diagnosis"
          />
        </div>

        <div className="editCard">
          <label>Differential Diagnoses</label>
          <textarea
            value={form.differential_diagnoses}
            onChange={(e) => updateField("differential_diagnoses", e.target.value)}
            placeholder="One point per line"
          />
        </div>

        <div className="editCard fullWidthClinicalCard">
          <label>Clinical Reasoning</label>
          <textarea
            value={form.clinical_reasoning}
            onChange={(e) => updateField("clinical_reasoning", e.target.value)}
            placeholder="Clinical reasoning"
          />
        </div>

        <div className="editCard fullWidthClinicalCard">
          <label>Management Plan JSON</label>
          <textarea
            value={form.management_plan}
            onChange={(e) => updateField("management_plan", e.target.value)}
            placeholder="Management plan JSON"
          />
        </div>

        <div className="editCard">
          <label>Complications to Watch</label>
          <textarea
            value={form.complications_to_watch}
            onChange={(e) => updateField("complications_to_watch", e.target.value)}
            placeholder="One point per line"
          />
        </div>

        <div className="editCard">
          <label>Red Flags</label>
          <textarea
            value={form.red_flags}
            onChange={(e) => updateField("red_flags", e.target.value)}
            placeholder="One point per line"
          />
        </div>

        <div className="editCard fullWidthClinicalCard">
          <label>Prognosis</label>
          <textarea
            value={form.prognosis}
            onChange={(e) => updateField("prognosis", e.target.value)}
            placeholder="Prognosis"
          />
        </div>

        <div className="editCard fullWidthClinicalCard">
          <label>Missing Information Needed</label>
          <textarea
            value={form.missing_information_needed}
            onChange={(e) => updateField("missing_information_needed", e.target.value)}
            placeholder="One point per line"
          />
        </div>

        <div className="editCard fullWidthClinicalCard safetyNoteCard">
          <label>Safety Note</label>
          <textarea
            value={form.safety_note}
            onChange={(e) => updateField("safety_note", e.target.value)}
            placeholder="Safety note"
          />
        </div>
      </div>

      <div className="editActions">
        <button disabled={saving} onClick={() => save("draft")}>
          {saving ? "Saving..." : "Save Draft"}
        </button>

        <button disabled={saving} className="publishBtn" onClick={() => save("published")}>
          {saving ? "Publishing..." : "Save & Publish"}
        </button>
      </div>

      {message && <p className="editMessage">{message}</p>}
    </div>
  );
}

function AdminPage() {
  const [activeTab, setActiveTab] = useState("upload");
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  function openTab(tab) {
    setActiveTab(tab);
    setMobileOpen(false);
  }

  function openEdit(caseId) {
    setSelectedCaseId(caseId);
    setActiveTab("edit");
  }

  return (
    <section className="adminLayout">
      <button className="mobileMenuBtn" onClick={() => setMobileOpen(!mobileOpen)}>
        ☰ CCL Intelligence
      </button>

      <aside className={mobileOpen ? "adminSidebar open" : "adminSidebar"}>
        <div className="adminBrand">
          <img src="/logo.png" alt="DocTutorials" />
          <h2>CCL Intelligence</h2>
        </div>

        <button
          className={activeTab === "upload" ? "sidebarBtn active" : "sidebarBtn"}
          onClick={() => openTab("upload")}
        >
          Upload Case
        </button>

        <button
          className={activeTab === "dashboard" ? "sidebarBtn active" : "sidebarBtn"}
          onClick={() => openTab("dashboard")}
        >
          Manage Uploads
        </button>

        <button
          className={activeTab === "edit" ? "sidebarBtn active" : "sidebarBtn"}
          onClick={() => openTab("edit")}
        >
          Edit & Publish
        </button>
      </aside>

      {mobileOpen && <div className="mobileOverlay" onClick={() => setMobileOpen(false)} />}

      <main className="adminMainContent">
        {activeTab === "upload" && <UploadCase />}
        {activeTab === "dashboard" && <ManageUploads openEdit={openEdit} />}
        {activeTab === "edit" && <EditPublish selectedCaseId={selectedCaseId} />}
      </main>
    </section>
  );
}

function CasePage({ navigateHome }) {
  const { caseId } = useParams();

  const [caseData, setCaseData] = useState(null);
  const [files, setFiles] = useState([]);
  const [activeTab, setActiveTab] = useState("ai");

  async function loadCase() {
    const response = await api.get(`/cases/${caseId}?t=${Date.now()}`);
    setCaseData(response.data);

    try {
      const fileResponse = await api.get(`/case-files/${caseId}?t=${Date.now()}`);
      setFiles(Array.isArray(fileResponse.data) ? fileResponse.data : []);
    } catch {
      setFiles([]);
    }
  }

  useEffect(() => {
    loadCase();
  }, [caseId]);

  if (!caseData) {
    return <div className="casePage">Loading case...</div>;
  }

  const rootAI = parseAI(caseData.ai_summary);
  const ai = rootAI.extracted_facts || rootAI;
  const reconstructed = rootAI.ai_reconstructed_case || {};
  const teachingCase = reconstructed.ai_reconstructed_teaching_case || {};
  const structured = ai.structured_sections || {};

  const labReports = files.filter((f) => f.file_type === "lab_report");
  const images = files.filter((f) => f.file_type === "image");
  const videos = files.filter((f) => f.file_type === "video");

  return (
    <div className="casePage">
      <div className="caseTop">
        <button className="backBtn" onClick={navigateHome}>
          ← Back to Cases
        </button>

        <p>{caseData.status || "draft"} Clinical Case</p>
        <h1>{caseData.case_title || "Untitled Case"}</h1>
      </div>

      <div className="caseLayout">
        <aside className="caseSideMenu">
          {[
            ["ai", "AI Clinical Interpretation"],
            ["labs", "Lab Reports"],
            ["images", "Image"],
            ["videos", "Videos"],
            ["flowchart", "Flow Chart"],
            ["qhub", "Q-Hub"],
            ["conclusion", "Clinical Impression & Conclusion"],
          ].map(([key, label]) => (
            <button
              key={key}
              className={activeTab === key ? "sectionBtn active" : "sectionBtn"}
              onClick={() => setActiveTab(key)}
            >
              {label}
            </button>
          ))}
        </aside>

        <main className="caseSummaryPanel">
          {activeTab === "ai" && (
            <>
              <h2>AI Clinical Interpretation</h2>

              <div className="clinicalSummaryGrid">
                <Section title="History & Presenting Complaints">
                  <BulletList items={structured.history_presenting_complaints} />
                </Section>

                <Section title="Clinical Examination & Diagnostics">
                  <BulletList items={structured.clinical_examination_diagnostics} />
                </Section>

                <Section title="Management / Treatment Plan">
                  <BulletList items={structured.management_treatment_plan} />
                </Section>

                <Section title="Patient History">
                  <p>{teachingCase.history_of_presenting_illness || ai.patient_history || "Not clearly documented."}</p>
                </Section>

                <Section title="Clinical Findings">
                  <p>{teachingCase.clinical_reasoning || ai.clinical_findings || "Not clearly documented."}</p>
                </Section>

                <Section title="Clinical Significance">
                  <p>{ai.clinical_significance || "Not clearly documented."}</p>
                </Section>

                <Section title="Planned Procedure">
                  <pre>{teachingCase.management_plan ? JSON.stringify(teachingCase.management_plan, null, 2) : ai.planned_procedure || "Not clearly documented."}</pre>
                </Section>
              </div>
            </>
          )}

          {activeTab === "labs" && (
            <>
              <h2>Lab Reports</h2>
              {labReports.length ? (
                <div className="mediaList">
                  {labReports.map((file) => (
                    <a
                      key={file.id}
                      href={`http://localhost:8001/storage/${file.filename}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      📄 {file.original_name || file.filename}
                    </a>
                  ))}
                </div>
              ) : (
                <p>No lab reports uploaded.</p>
              )}
            </>
          )}

          {activeTab === "images" && (
            <>
              <h2>Images</h2>
              {images.length ? (
                <div className="imageGallery">
                  {images.map((file) => (
                    <img
                      key={file.id}
                      src={`http://localhost:8001/storage/${file.filename}`}
                      alt={file.filename}
                      className="caseImage"
                    />
                  ))}
                </div>
              ) : (
                <p>No images uploaded.</p>
              )}
            </>
          )}

          {activeTab === "videos" && (
            <>
              <h2>Videos</h2>
              {videos.length ? (
                <div className="videoGrid">
                  {videos.map((file) => (
                    <video
                      key={file.id}
                      controls
                      className="caseVideo"
                      src={`http://localhost:8001/storage/${file.filename}`}
                    />
                  ))}
                </div>
              ) : (
                <p>No videos uploaded.</p>
              )}
            </>
          )}

          {activeTab === "flowchart" && (
            <>
              <h2>Flow Chart</h2>
              <BulletList
                items={(ai.flowchart || []).map((item) =>
                  typeof item === "string"
                    ? item
                    : `${item.step || "Step"}: ${item.description || ""}`
                )}
              />
            </>
          )}

          {activeTab === "qhub" && (
            <>
              <h2>Q-Hub</h2>
              <BulletList
                items={(ai.qhub_questions || []).map((item) =>
                  typeof item === "string"
                    ? item
                    : `${item.type || "Question"}: ${item.question || ""}`
                )}
              />
            </>
          )}

          {activeTab === "conclusion" && (
            <>
              <h2>Clinical Impression & Conclusion</h2>
              <Section title="Conclusion">
                <p>{ai.conclusion || reconstructed.safety_note || "Faculty review is recommended."}</p>
              </Section>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  function navigateToCase(caseId) {
    navigate(`/case/${caseId}`);
  }

  function navigateHome() {
    navigate("/");
  }

  function goTo(path) {
    navigate(path);
    setMenuOpen(false);
  }

  return (
    <div className="appRoot">
      <button className="sidebarToggle" onClick={() => setMenuOpen(true)}>
        ☰
      </button>

      {menuOpen && (
        <>
          <div className="sidebarBackdrop" onClick={() => setMenuOpen(false)} />

          <aside className="globalSidebar">
            <div className="sidebarBrand">
              <div className="textLogo">DocTutorials</div>
              <h1>CCL Intelligence</h1>
            </div>

            <button onClick={() => goTo("/")}>User Library</button>
            <button onClick={() => goTo("/admin")}>Admin Panel</button>
          </aside>
        </>
      )}

      <main className="mainWorkspace">
        <Routes>
          <Route path="/" element={<LibraryPage navigateToCase={navigateToCase} />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/case/:caseId" element={<CasePage navigateHome={navigateHome} />} />
        </Routes>
      </main>
    </div>
  );
}
