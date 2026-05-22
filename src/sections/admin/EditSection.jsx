import { useEffect, useState } from "react";

import {
  getCase,
  updateCaseAI,
  updateCaseStatus
} from "../../services/caseService";

const EMPTY_SUMMARY = {
  history: "",
  findings: "",
  significance: "",
  procedure_plan: "",
  conclusion: "",
  keywords: [],
  clinical_notes: [],
  flowchart: []
};

export default function EditSection({ selectedCaseId }) {
  const [caseData, setCaseData] = useState(null);
  const [summary, setSummary] = useState(EMPTY_SUMMARY);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (selectedCaseId) loadCase();
  }, [selectedCaseId]);

  async function loadCase() {
    const data = await getCase(selectedCaseId);

    const parsedSummary =
      typeof data.ai_summary === "string"
        ? JSON.parse(data.ai_summary)
        : data.ai_summary || EMPTY_SUMMARY;

    setCaseData(data);
    setSummary({
      ...EMPTY_SUMMARY,
      ...parsedSummary
    });
  }

  function updateField(field, value) {
    setSummary({
      ...summary,
      [field]: value
    });
  }

  function addClinicalNote() {
    setSummary({
      ...summary,
      clinical_notes: [
        ...(summary.clinical_notes || []),
        { day: "", progress: "", medication: "", vitals: "" }
      ]
    });
  }

  function updateClinicalNote(index, field, value) {
    const notes = [...(summary.clinical_notes || [])];

    notes[index] = {
      ...notes[index],
      [field]: value
    };

    updateField("clinical_notes", notes);
  }

  function removeClinicalNote(index) {
    const notes = [...(summary.clinical_notes || [])];
    notes.splice(index, 1);
    updateField("clinical_notes", notes);
  }

  function addFlowStep() {
    setSummary({
      ...summary,
      flowchart: [
        ...(summary.flowchart || []),
        { step: "", description: "" }
      ]
    });
  }

  function updateFlowStep(index, field, value) {
    const flow = [...(summary.flowchart || [])];

    flow[index] = {
      ...flow[index],
      [field]: value
    };

    updateField("flowchart", flow);
  }

  function removeFlowStep(index) {
    const flow = [...(summary.flowchart || [])];
    flow.splice(index, 1);
    updateField("flowchart", flow);
  }

  async function saveEdits() {
    if (!selectedCaseId) {
      alert("Please select a case first");
      return;
    }

    setSaving(true);

    try {
      const response = await updateCaseAI(selectedCaseId, summary);
      setSummary(response.ai_summary || summary);
      alert("All sections saved successfully");
    } catch (error) {
      console.error(error);
      alert("Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function publishCase() {
    await saveEdits();
    await updateCaseStatus(selectedCaseId, "published");
    alert("Case published successfully");
  }

  async function saveDraft() {
    await saveEdits();
    await updateCaseStatus(selectedCaseId, "draft");
    alert("Case saved as draft");
  }

  if (!selectedCaseId) {
    return (
      <div className="adminCard">
        <h2>Select a case from Manage Uploads</h2>
      </div>
    );
  }

  return (
    <div className="adminCard">
      <h1>Edit & Publish Case</h1>

      <p>
        <strong>{caseData?.case_title}</strong> | Case ID: {selectedCaseId}
      </p>

      <EditBlock
        title="History"
        value={summary.history}
        onChange={(value) => updateField("history", value)}
      />

      <EditBlock
        title="Findings"
        value={summary.findings}
        onChange={(value) => updateField("findings", value)}
      />

      <EditBlock
        title="Significance"
        value={summary.significance}
        onChange={(value) => updateField("significance", value)}
      />

      <EditBlock
        title="Planned Procedure"
        value={summary.procedure_plan}
        onChange={(value) => updateField("procedure_plan", value)}
      />

      <EditBlock
        title="Conclusion"
        value={summary.conclusion}
        onChange={(value) => updateField("conclusion", value)}
      />

      <div className="summaryCard">
        <h3>Keywords</h3>

        <textarea
          className="editTextarea"
          value={(summary.keywords || []).join(", ")}
          onChange={(e) =>
            updateField(
              "keywords",
              e.target.value
                .split(",")
                .map((x) => x.trim())
                .filter(Boolean)
            )
          }
        />
      </div>

      <div className="summaryCard">
        <div className="summaryCardHeader">
          <h3>Clinical Notes</h3>
          <button type="button" onClick={addClinicalNote}>
            + Add Note
          </button>
        </div>

        {(summary.clinical_notes || []).map((note, index) => (
          <div key={index} className="clinicalNoteEdit">
            <input
              placeholder="Day"
              value={note.day || ""}
              onChange={(e) =>
                updateClinicalNote(index, "day", e.target.value)
              }
            />

            <textarea
              placeholder="Progress"
              value={note.progress || ""}
              onChange={(e) =>
                updateClinicalNote(index, "progress", e.target.value)
              }
            />

            <textarea
              placeholder="Medication"
              value={note.medication || ""}
              onChange={(e) =>
                updateClinicalNote(index, "medication", e.target.value)
              }
            />

            <textarea
              placeholder="Vitals"
              value={note.vitals || ""}
              onChange={(e) =>
                updateClinicalNote(index, "vitals", e.target.value)
              }
            />

            <button
              type="button"
              className="deleteBtn"
              onClick={() => removeClinicalNote(index)}
            >
              Remove Note
            </button>
          </div>
        ))}
      </div>

      <div className="summaryCard">
        <div className="summaryCardHeader">
          <h3>Flowchart</h3>
          <button type="button" onClick={addFlowStep}>
            + Add Step
          </button>
        </div>

        {(summary.flowchart || []).map((item, index) => (
          <div key={index} className="clinicalNoteEdit">
            <input
              placeholder="Step"
              value={item.step || ""}
              onChange={(e) =>
                updateFlowStep(index, "step", e.target.value)
              }
            />

            <textarea
              placeholder="Description"
              value={item.description || ""}
              onChange={(e) =>
                updateFlowStep(index, "description", e.target.value)
              }
            />

            <button
              type="button"
              className="deleteBtn"
              onClick={() => removeFlowStep(index)}
            >
              Remove Step
            </button>
          </div>
        ))}
      </div>

      <div className="actionRow">
        <button onClick={saveEdits} disabled={saving}>
          {saving ? "Saving..." : "Save All Edits"}
        </button>

        <button onClick={saveDraft}>
          Save Draft
        </button>

        <button onClick={publishCase}>
          Save & Publish
        </button>
      </div>
    </div>
  );
}

function EditBlock({ title, value, onChange }) {
  return (
    <div className="summaryCard">
      <h3>{title}</h3>

      <textarea
        className="editTextarea"
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
