import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  FaFileMedical,
  FaHeartbeat,
  FaImage,
  FaVideo,
  FaNotesMedical,
  FaProjectDiagram,
  FaQuestionCircle,
  FaCheckCircle,
} from "react-icons/fa";

import api from "../services/api";
import { getCaseFiles } from "../services/caseService";

const sections = [
  {
    key: "ai",
    label: "AI Clinical Interpretation",
    icon: <FaFileMedical />,
  },
  {
    key: "labs",
    label: "Lab Reports",
    icon: <FaHeartbeat />,
  },
  {
    key: "images",
    label: "Image",
    icon: <FaImage />,
  },
  {
    key: "videos",
    label: "Videos",
    icon: <FaVideo />,
  },
  {
    key: "notes",
    label: "Patient Clinical Progress Notes",
    icon: <FaNotesMedical />,
  },
  {
    key: "flowchart",
    label: "Flow Chart",
    icon: <FaProjectDiagram />,
  },
  {
    key: "qhub",
    label: "Q-Hub",
    icon: <FaQuestionCircle />,
  },
  {
    key: "conclusion",
    label: "Clinical Impression & Conclusion",
    icon: <FaCheckCircle />,
  },
];

function parseSummary(value) {
  if (!value) return {};

  if (typeof value === "object") {
    return value;
  }

  if (typeof value === "string") {
    try {
      return JSON.parse(value);
    } catch {
      return {};
    }
  }

  return {};
}

function valueOrDefault(value) {
  if (Array.isArray(value)) {
    return value.length ? value : [];
  }

  if (value && String(value).trim()) {
    return value;
  }

  return "Not mentioned in the uploaded case sheet.";
}

function ClinicalCard({ title, children }) {
  return (
    <div className="smartClinicalCard">
      <h3>{title}</h3>
      <div className="clinicalCardBody">{children}</div>
    </div>
  );
}

function Paragraph({ value }) {
  return <p>{valueOrDefault(value)}</p>;
}

function BulletList({ items }) {
  if (!Array.isArray(items) || !items.length) {
    return <p>Not mentioned in the uploaded case sheet.</p>;
  }

  return (
    <div className="clinicalContentArea">
      {items.map((item, index) => (
        <div className="clinicalBullet" key={index}>
          <span className="clinicalDot"></span>
          <p>{item}</p>
        </div>
      ))}
    </div>
  );
}

function AIClinicalSection({ summary }) {
  return (
    <div className="clinicalSummaryGrid">
      <ClinicalCard title="Case Overview">
        <Paragraph value={summary.case_overview} />
      </ClinicalCard>

      <ClinicalCard title="Key Clinical History">
        <Paragraph value={summary.key_clinical_history} />
      </ClinicalCard>

      <ClinicalCard title="Examination & Findings">
        <Paragraph value={summary.examination_and_findings} />
      </ClinicalCard>

      <ClinicalCard title="Investigations">
        <Paragraph value={summary.investigations} />
      </ClinicalCard>

      <ClinicalCard title="Diagnosis / Impression">
        <Paragraph value={summary.diagnosis_or_impression} />
      </ClinicalCard>

      <ClinicalCard title="Management Plan">
        <Paragraph value={summary.management_plan} />
      </ClinicalCard>

      <div className="smartClinicalCard fullWidthClinicalCard">
        <h3>Teaching Points</h3>
        <BulletList items={summary.teaching_points} />
      </div>
    </div>
  );
}

function LabReportsSection({ files }) {
  if (!files.length) {
    return <p className="emptyState">No lab reports uploaded.</p>;
  }

  return (
    <div className="clinicalSummaryGrid">
      {files.map((file) => (
        <ClinicalCard key={file.id} title={file.filename || "Lab Report"}>
          {file.ai_analysis?.tests?.length ? (
            <table className="notesTable">
              <thead>
                <tr>
                  <th>Test</th>
                  <th>Value</th>
                  <th>Interpretation</th>
                </tr>
              </thead>
              <tbody>
                {file.ai_analysis.tests.map((test, index) => (
                  <tr key={index}>
                    <td>{test.test || "-"}</td>
                    <td>{test.value || "-"}</td>
                    <td>{test.interpretation || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No AI analysis available.</p>
          )}
        </ClinicalCard>
      ))}
    </div>
  );
}

function ImagesSection({ files }) {
  if (!files.length) {
    return <p className="emptyState">No images uploaded.</p>;
  }

  return (
    <div className="imageGallery">
      {files.map((file) => (
        <img
          key={file.id}
          src={`http://localhost:8001/storage/${file.filename}`}
          alt={file.filename}
          className="caseImage"
        />
      ))}
    </div>
  );
}

function VideosSection({ files }) {
  if (!files.length) {
    return <p className="emptyState">No videos uploaded.</p>;
  }

  return (
    <div className="videoGrid">
      {files.map((file) => (
        <video
          key={file.id}
          controls
          className="caseVideo"
          src={`http://localhost:8001/storage/${file.filename}`}
        />
      ))}
    </div>
  );
}

function NotesSection({ notes }) {
  if (!Array.isArray(notes) || !notes.length) {
    return <p className="emptyState">No clinical progress notes generated.</p>;
  }

  return (
    <table className="notesTable">
      <thead>
        <tr>
          <th>Date / Stage</th>
          <th>Clinical Note</th>
        </tr>
      </thead>
      <tbody>
        {notes.map((note, index) => (
          <tr key={index}>
            <td>{note.date || note.stage || `Note ${index + 1}`}</td>
            <td>{note.note || note.description || JSON.stringify(note)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function FlowchartSection({ flowchart }) {
  if (!Array.isArray(flowchart) || !flowchart.length) {
    return <p className="emptyState">No flowchart generated.</p>;
  }

  return (
    <div className="graphFlowWrap">
      {flowchart.map((step, index) => (
        <div className="graphFlowNode" key={index}>
          <h3>{step.step || `Step ${index + 1}`}</h3>
          <p>{step.description || "No description available."}</p>
        </div>
      ))}
    </div>
  );
}

function QHubSection({ summary }) {
  const questions = Array.isArray(summary.qhub_questions)
    ? summary.qhub_questions
    : [];

  const fallbackTeachingPoints = Array.isArray(summary.teaching_points)
    ? summary.teaching_points
    : [];

  if (!questions.length) {
    return <p className="emptyState">No Q-Hub content generated.</p>;
  }

  return (
    <div className="qhubGrid">
      {questions.map((item, index) => (
        <div className="qhubCard" key={index}>
          <span className="qhubType">{item.type || "Question"}</span>
          <p className="qhubQuestion">
            {item.question || item}
          </p>
        </div>
      ))}
    </div>
  );
}

function ConclusionSection({ summary }) {
  return (
    <div className="clinicalSummaryGrid">
      <ClinicalCard title="Diagnosis / Clinical Impression">
        <Paragraph value={summary.diagnosis_or_impression} />
      </ClinicalCard>

      <ClinicalCard title="Management Summary">
        <Paragraph value={summary.management_plan} />
      </ClinicalCard>

      <ClinicalCard title="Extraction Quality">
        <Paragraph value={summary.extraction_quality} />
      </ClinicalCard>

      <ClinicalCard title="Unreadable Sections">
        <Paragraph value={summary.unreadable_sections} />
      </ClinicalCard>
    </div>
  );
}

export default function CasePage({ navigateHome }) {
  const { caseId } = useParams();

  const [caseData, setCaseData] = useState(null);
  const [caseFiles, setCaseFiles] = useState([]);
  const [activeSection, setActiveSection] = useState("ai");

  async function loadCase() {
    const response = await api.get(`/cases/${caseId}?t=${Date.now()}`);
    setCaseData(response.data);

    const files = await getCaseFiles(caseId);
    setCaseFiles(Array.isArray(files) ? files : []);
  }

  useEffect(() => {
    loadCase();
  }, [caseId]);

  if (!caseData) {
    return <div className="casePage">Loading case...</div>;
  }

  const summary = parseSummary(caseData.ai_summary);

  const labReports = caseFiles.filter((file) => file.file_type === "lab_report");
  const images = caseFiles.filter((file) => file.file_type === "image");
  const videos = caseFiles.filter((file) => file.file_type === "video");

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
          {sections.map((section) => (
            <button
              key={section.key}
              className={
                activeSection === section.key
                  ? "sectionBtn active"
                  : "sectionBtn"
              }
              onClick={() => setActiveSection(section.key)}
            >
              <span className="iconWrap">{section.icon}</span>
              {section.label}
            </button>
          ))}
        </aside>

        <main className="caseSummaryPanel">
          {activeSection === "ai" && (
            <>
              <h2>AI Clinical Interpretation</h2>
              <AIClinicalSection summary={summary} />
            </>
          )}

          {activeSection === "labs" && (
            <>
              <h2>Lab Reports</h2>
              <LabReportsSection files={labReports} />
            </>
          )}

          {activeSection === "images" && (
            <>
              <h2>Images</h2>
              <ImagesSection files={images} />
            </>
          )}

          {activeSection === "videos" && (
            <>
              <h2>Videos</h2>
              <VideosSection files={videos} />
            </>
          )}

          {activeSection === "notes" && (
            <>
              <h2>Patient Clinical Progress Notes</h2>
              <NotesSection notes={summary.clinical_notes} />
            </>
          )}

          {activeSection === "flowchart" && (
            <>
              <h2>Flow Chart</h2>
              <FlowchartSection flowchart={summary.flowchart} />
            </>
          )}

          {activeSection === "qhub" && (
            <>
              <h2>Q-Hub</h2>
              <QHubSection summary={summary} />
            </>
          )}

          {activeSection === "conclusion" && (
            <>
              <h2>Clinical Impression & Conclusion</h2>
              <ConclusionSection summary={summary} />
            </>
          )}
        </main>
      </div>
    </div>
  );
}
