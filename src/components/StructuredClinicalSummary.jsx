import React from "react";

function parseContent(text = "") {
  return String(text || "")
    .replace(/\n/g, " ")
    .replace(/\s-\s/g, ". ")
    .replace(/•/g, ". ")
    .split(/\.(?=\s|$)/)
    .map((x) => x.trim())
    .filter((x) => x.length > 5);
}

function Section({ title, text }) {
  const items = parseContent(text);

  return (
    <div className="smartClinicalCard">
      <h3>{title}</h3>

      <div className="clinicalContentArea">
        {items.map((item, idx) => (
          <div className="clinicalBullet" key={idx}>
            <span className="clinicalDot"></span>

            <p>
              {item}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function StructuredClinicalSummary({ summary }) {
  return (
    <div className="clinicalSummaryGrid">

      <Section
        title="Patient History & Clinical Context"
        text={summary?.history}
      />

      <Section
        title="Detailed Clinical Findings"
        text={summary?.findings}
      />

      <Section
        title="Clinical Significance & Interpretation"
        text={summary?.significance}
      />

      <Section
        title="Planned Procedure"
        text={summary?.procedure_plan}
      />

    </div>
  );
}
