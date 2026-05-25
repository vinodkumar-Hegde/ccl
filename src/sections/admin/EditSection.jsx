import { useEffect, useState } from "react";
import api from "../../services/api";

const SUMMARY_FIELDS = [
  {
    key: "case_overview",
    label: "Case Overview",
  },
  {
    key: "key_clinical_history",
    label: "Key Clinical History",
  },
  {
    key: "examination_and_findings",
    label: "Examination & Findings",
  },
  {
    key: "investigations",
    label: "Investigations",
  },
  {
    key: "diagnosis_or_impression",
    label: "Diagnosis / Impression",
  },
  {
    key: "management_plan",
    label: "Management Plan",
  },
  {
    key: "extraction_quality",
    label: "Extraction Quality",
  },
  {
    key: "unreadable_sections",
    label: "Unreadable Sections",
  },
];

export default function EditSection() {
  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState("");
  const [selectedCase, setSelectedCase] = useState(null);
  const [summary, setSummary] = useState({});
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  async function loadCases() {
    try {
      const response = await api.get(`/cases/?t=${Date.now()}`);
      const list = Array.isArray(response.data) ? response.data : [];

      setCases(list);

      if (list.length && !selectedCaseId) {
        selectCase(list[0]);
      }
    } catch (error) {
      console.error("Failed to load cases", error);
      setMessage("Failed to load cases.");
    }
  }

  function selectCase(caseItem) {
    setSelectedCase(caseItem);
    setSelectedCaseId(String(caseItem.id));

    const ai = caseItem.ai_summary || {};

    setSummary({
      case_overview: ai.case_overview || ai.history || "",
      key_clinical_history: ai.key_clinical_history || ai.clinical_history || "",
      examination_and_findings: ai.examination_and_findings || ai.findings || "",
      investigations: ai.investigations || "",
      diagnosis_or_impression: ai.diagnosis_or_impression || ai.conclusion || "",
      management_plan: ai.management_plan || ai.procedure_plan || "",
      extraction_quality: ai.extraction_quality || "",
      unreadable_sections: ai.unreadable_sections || "",
    });

    setMessage("");
  }

  function handleCaseChange(event) {
    const id = event.target.value;
    const found = cases.find((item) => String(item.id) === String(id));

    if (found) {
      selectCase(found);
    }
  }

  function updateField(key, value) {
    setSummary((prev) => ({
      ...prev,
      [key]: value,
    }));
  }

  async function saveCase(status = null) {
    if (!selectedCase) {
      setMessage("Please select a case first.");
      return;
    }

    setSaving(true);
    setMessage("");

    const updatedSummary = {
      ...selectedCase.ai_summary,
      ...summary,
    };

    try {
      await api.put(`/case-ai/${selectedCase.id}`, {
        ai_summary: updatedSummary,
        status,
      });

      setMessage(
        status === "published"
          ? "Saved and published successfully."
          : "Saved successfully."
      );

      await loadCases();
    } catch (error) {
      console.error("Save failed", error);
      setMessage("Save failed. Check backend logs.");
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    loadCases();
  }, []);

  return (
    <div className="editPublishPage">
      <h1>Edit & Publish Case</h1>

      <div className="editTopBar">
        <label>Select Case</label>

        <select value={selectedCaseId} onChange={handleCaseChange}>
          {cases.map((item) => (
            <option key={item.id} value={item.id}>
              {item.case_title || item.title || `Case ${item.id}`} | ID: {item.id}
            </option>
          ))}
        </select>
      </div>

      {selectedCase && (
        <p className="editCaseMeta">
          <strong>{selectedCase.case_title || selectedCase.title}</strong>
          {" "} | Case ID: {selectedCase.id}
          {" "} | Status: {selectedCase.status || "draft"}
          {" "} | Processing: {selectedCase.processing_status || "unknown"}
        </p>
      )}

      <div className="editGrid">
        {SUMMARY_FIELDS.map((field) => (
          <div className="editCard" key={field.key}>
            <label>{field.label}</label>

            <textarea
              value={summary[field.key] || ""}
              onChange={(event) => updateField(field.key, event.target.value)}
              placeholder={`Enter ${field.label}`}
            />
          </div>
        ))}

        <div className="editCard fullWidthEditCard">
          <label>Teaching Points</label>

          <textarea
            value={teachingPoints}
            onChange={(event) => setTeachingPoints(event.target.value)}
            placeholder="Enter one teaching point per line"
          />
        </div>
      </div>

      <div className="editActions">
        <button disabled={saving} onClick={() => saveCase(null)}>
          {saving ? "Saving..." : "Save Draft"}
        </button>

        <button
          disabled={saving}
          className="publishBtn"
          onClick={() => saveCase("published")}
        >
          {saving ? "Publishing..." : "Save & Publish"}
        </button>
      </div>

      {message && <p className="editMessage">{message}</p>}
    </div>
  );
}
