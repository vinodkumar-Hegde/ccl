function parseSummary(summary) {
  if (!summary) return {};

  if (typeof summary === "string") {
    try {
      return JSON.parse(summary);
    } catch {
      return {};
    }
  }

  if (typeof summary === "object") {
    return summary;
  }

  return {};
}

function getValue(summary, keys) {
  for (const key of keys) {
    if (summary?.[key] && String(summary[key]).trim()) {
      return summary[key];
    }
  }

  return "Not mentioned in the uploaded case sheet.";
}

function TextCard({ title, value }) {
  return (
    <div className="smartClinicalCard">
      <h3>{title}</h3>
      <p>{value || "Not mentioned in the uploaded case sheet."}</p>
    </div>
  );
}

export default function StructuredClinicalSummary({ summary }) {
  const ai = parseSummary(summary);

  const teachingPoints = Array.isArray(ai.teaching_points)
    ? ai.teaching_points
    : [];

  return (
    <div className="clinicalSummaryGrid">
      <TextCard
        title="Case Overview"
        value={getValue(ai, ["case_overview", "history"])}
      />

      <TextCard
        title="Key Clinical History"
        value={getValue(ai, ["key_clinical_history", "clinical_history", "history"])}
      />

      <TextCard
        title="Examination & Findings"
        value={getValue(ai, ["examination_and_findings", "findings"])}
      />

      <TextCard
        title="Investigations"
        value={getValue(ai, ["investigations"])}
      />

      <TextCard
        title="Diagnosis / Impression"
        value={getValue(ai, ["diagnosis_or_impression", "clinical_impression", "conclusion"])}
      />

      <TextCard
        title="Management Plan"
        value={getValue(ai, ["management_plan", "procedure_plan"])}
      />

      <div className="smartClinicalCard fullWidthClinicalCard">
        <h3>Teaching Points</h3>

        {teachingPoints.length ? (
          <div className="clinicalContentArea">
            {teachingPoints.map((point, index) => (
              <div className="clinicalBullet" key={index}>
                <span className="clinicalDot"></span>
                <p>{point}</p>
              </div>
            ))}
          </div>
        ) : (
          <p>Not mentioned in the uploaded case sheet.</p>
        )}
      </div>

      <TextCard
        title="Extraction Quality"
        value={getValue(ai, ["extraction_quality"])}
      />

      <TextCard
        title="Unreadable Sections"
        value={getValue(ai, ["unreadable_sections"])}
      />
    </div>
  );
}
