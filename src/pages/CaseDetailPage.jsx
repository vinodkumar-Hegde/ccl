import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../services/api";

const API_BASE = "http://localhost:8001";

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

  if (Array.isArray(value)) {
    return value.map(toText).filter(Boolean);
  }

  return [toText(value)].filter(Boolean);
}

function Section({ title, children }) {
  return (
    <section className="caseDetailSection">
      <h2>{title}</h2>
      <div className="caseDetailContent">{children}</div>
    </section>
  );
}

function BulletList({ items }) {
  const list = cleanList(items);

  if (list.length === 0) {
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

export default function CaseDetailPage({ navigateHome }) {
  const { caseId } = useParams();

  const [caseData, setCaseData] = useState(null);
  const [media, setMedia] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCase();
  }, [caseId]);

  async function loadCase() {
    try {
      setLoading(true);

      const response = await api.get(`/cases/${caseId}`);
      setCaseData(response.data);

      try {
        const mediaResponse = await api.get(`/case-media/${caseId}`);
        setMedia(Array.isArray(mediaResponse.data) ? mediaResponse.data : []);
      } catch {
        setMedia([]);
      }
    } catch (error) {
      console.error("Case loading failed", error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="caseDetailPage">Loading case...</div>;
  }

  if (!caseData) {
    return <div className="caseDetailPage">Case not found.</div>;
  }

  const ai = caseData.ai_summary || {};
  const structured = ai.structured_sections || {};

  const images = media.filter((m) => m.media_type === "image");
  const videos = media.filter((m) => m.media_type === "video");
  const labReports = media.filter((m) => m.media_type === "lab_report");

  return (
    <div className="caseDetailPage">
      <button className="backBtn" onClick={navigateHome}>
        ← Back to Cases
      </button>

      <div className="caseHero">
        <div>
          <p className="caseEyebrow">Published Clinical Case</p>
          <h1>{caseData.case_title || "Untitled Case"}</h1>

          <div className="caseMetaRow">
            <span>{caseData.subject || "Subject not added"}</span>
            <span>{caseData.speciality || "Speciality not added"}</span>
            <span>{caseData.disease || "Disease not added"}</span>
          </div>
        </div>
      </div>

      <Section title="Obstetric History & Presenting Complaints">
        <BulletList items={structured.obstetric_history_presenting_complaints} />
      </Section>

      <Section title="Pre-operative Clinical Findings & Diagnostics">
        <BulletList items={structured.preoperative_clinical_findings_diagnostics} />
      </Section>

      <Section title="Delivery & Operative Details">
        <BulletList items={structured.delivery_operative_details} />
      </Section>

      <Section title="Patient History">
        <p>{ai.patient_history || "Not clearly documented."}</p>
      </Section>

      <Section title="Clinical Findings">
        <p>{ai.clinical_findings || "Not clearly documented."}</p>
      </Section>

      <Section title="Clinical Significance">
        <p>{ai.clinical_significance || "Not clearly documented."}</p>
      </Section>

      <Section title="Planned Procedure">
        <p>{ai.planned_procedure || "Not clearly documented."}</p>
      </Section>

      <Section title="Lab Reports">
        {labReports.length === 0 ? (
          <p>No lab reports uploaded for this case.</p>
        ) : (
          <div className="mediaList">
            {labReports.map((file) => (
              <a
                key={file.id}
                href={`${API_BASE}/${file.file_path}`}
                target="_blank"
                rel="noreferrer"
              >
                📄 {file.file_name}
              </a>
            ))}
          </div>
        )}
      </Section>

      <Section title="Images">
        {images.length === 0 ? (
          <p>No clinical images uploaded for this case.</p>
        ) : (
          <div className="mediaGrid">
            {images.map((file) => (
              <a
                key={file.id}
                className="mediaImageCard"
                href={`${API_BASE}/${file.file_path}`}
                target="_blank"
                rel="noreferrer"
              >
                <img src={`${API_BASE}/${file.file_path}`} alt={file.file_name} />
                <span>{file.file_name}</span>
              </a>
            ))}
          </div>
        )}
      </Section>

      <Section title="Videos">
        {videos.length === 0 ? (
          <p>No clinical videos uploaded for this case.</p>
        ) : (
          <div className="mediaGrid">
            {videos.map((file) => (
              <div key={file.id} className="mediaVideoCard">
                <video src={`${API_BASE}/${file.file_path}`} controls />
                <span>{file.file_name}</span>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="Flow Chart">
        <BulletList
          items={(ai.flowchart || []).map((item) =>
            typeof item === "string"
              ? item
              : `${item.step || "Step"}: ${item.description || ""}`
          )}
        />
      </Section>

      <Section title="Q-Hub">
        <BulletList
          items={(ai.qhub_questions || []).map((item) =>
            typeof item === "string"
              ? item
              : `${item.type || "Question"}: ${item.question || ""}`
          )}
        />
      </Section>

      <Section title="Clinical Impression & Conclusion">
        <p>{ai.conclusion || "Faculty review is recommended."}</p>
      </Section>
    </div>
  );
}
