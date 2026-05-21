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
  clinical_notes: []
};

export default function EditSection({
  selectedCaseId
}) {
  const [summary, setSummary] =
    useState(EMPTY_SUMMARY);

  const [caseData, setCaseData] =
    useState(null);

  useEffect(() => {
    if (selectedCaseId) {
      loadCase();
    }
  }, [selectedCaseId]);

  async function loadCase() {
    const data = await getCase(
      selectedCaseId
    );

    setCaseData(data);

    setSummary(
      data.ai_summary || EMPTY_SUMMARY
    );
  }

  async function saveEdits() {
    await updateCaseAI(
      selectedCaseId,
      summary
    );

    alert("Saved");
  }

  async function publishCase() {
    await saveEdits();

    await updateCaseStatus(
      selectedCaseId,
      "published"
    );

    alert("Published");
  }

  if (!selectedCaseId) {
    return (
      <div className="adminCard">
        <h2>
          Select case from dashboard
        </h2>
      </div>
    );
  }

  return (
    <div className="adminCard">
      <h1>
        Edit & Publish Case
      </h1>

      <p>
        {caseData?.case_title}
      </p>

      <textarea
        className="editTextarea"
        value={summary.history || ""}
        onChange={(e) =>
          setSummary({
            ...summary,
            history: e.target.value
          })
        }
        placeholder="History"
      />

      <textarea
        className="editTextarea"
        value={summary.findings || ""}
        onChange={(e) =>
          setSummary({
            ...summary,
            findings: e.target.value
          })
        }
        placeholder="Findings"
      />

      <div className="actionRow">
        <button onClick={saveEdits}>
          Save Edits
        </button>

        <button onClick={publishCase}>
          Publish
        </button>
      </div>
    </div>
  );
}
