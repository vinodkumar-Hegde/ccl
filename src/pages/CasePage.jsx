import StructuredClinicalSummary from "../components/StructuredClinicalSummary";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import {
  FaFileMedical,
  FaHeartbeat,
  FaNotesMedical,
  FaProjectDiagram,
  FaQuestionCircle,
  FaCheckCircle,
  FaHospital,
  FaArrowLeft,
  FaVideo
} from "react-icons/fa";

import api from "../services/api";
import { getCaseFiles } from "../services/caseService";

const API_BASE_URL = "http://127.0.0.1:8001";

const caseSections = [
  { name: "AI Clinical Interpretation", icon: <FaFileMedical /> },
  { name: "Lab Reports", icon: <FaHeartbeat /> },
  { name: "Image", icon: <FaHospital /> },
  { name: "Videos", icon: <FaVideo /> },
  { name: "Patient Clinical Progress Notes", icon: <FaNotesMedical /> },
  { name: "Flow Chart", icon: <FaProjectDiagram /> },
  { name: "Q-Hub", icon: <FaQuestionCircle /> },
  { name: "Clinical Impression & Conclusion", icon: <FaCheckCircle /> }
];


function getFlowIcon(type = "") {
  const map = {
    start: "🧑‍⚕️",
    assessment: "🩺",
    investigation: "🧪",
    decision: "🔀",
    treatment: "💊",
    followup: "📅",
    outcome: "✅"
  };

  return map[type] || "📌";
}

function cleanFileName(name = "") {
  return name.replace(/\.[^/.]+$/, "");
}


function formatClinicalText(text = "") {
  return text
    .split(/\n|\.\s+/)
    .filter(Boolean)
    .map((item, index) => (
      <li key={index}>{item.trim()}</li>
    ));
}


function splitClinicalText(text = "") {
  return String(text || "Not mentioned")
    .replace(/\s-\s/g, "\n")
    .replace(/-\s+/g, "\n")
    .replace(/\.\s+/g, ".\n")
    .split(/\n+/)
    .map((x) => x.trim())
    .filter(Boolean);
}

function highlightKeywords(text = "", keywords = []) {
  if (!keywords || !keywords.length) return text;

  let parts = [text];

  keywords
    .map((k) => String(k).replace("-", "").trim())
    .filter((k) => k.length > 3)
    .slice(0, 12)
    .forEach((keyword) => {
      parts = parts.flatMap((part) => {
        if (typeof part !== "string") return [part];

        const regex = new RegExp(`(${keyword})`, "gi");
        return part.split(regex).map((piece, index) =>
          regex.test(piece) ? (
            <mark key={`${keyword}-${index}`} className="clinicalKeyword">
              {piece}
            </mark>
          ) : (
            piece
          )
        );
      });
    });

  return parts;
}

function SmartClinicalCard({ title, text, keywords }) {
  const points = splitClinicalText(text);

  return (
    <article className="smartClinicalCard">
      <h3>{title}</h3>

      {points.length <= 2 ? (
        <div className="clinicalParagraphBlock">
          {points.map((point, index) => (
            <p key={index}>
              {highlightKeywords(point, keywords)}
            </p>
          ))}
        </div>
      ) : (
        <ul className="smartClinicalList">
          {points.map((point, index) => (
            <li key={index}>
              {highlightKeywords(point, keywords)}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

export default function CasePage
({ navigateHome }) {
  const { caseId } = useParams();

  const [activeSection, setActiveSection] = useState("AI Clinical Interpretation");
  const [caseData, setCaseData] = useState(null);
  const [caseFiles, setCaseFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  async function loadCase() {
    try {
      const caseResponse = await api.get(`/cases/${caseId}?t=${Date.now()}`);
      const filesResponse = await getCaseFiles(caseId);

      setCaseData(caseResponse.data);
      setCaseFiles(filesResponse);
    } catch (error) {
      console.error(error);
      alert("Failed to load case");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCase();
  }, [caseId]);

  if (loading) {
    return <p>Loading case...</p>;
  }

  if (!caseData) {
    return <p>Case not found.</p>;
  }

  const summary =
  typeof caseData.ai_summary === "string"
    ? JSON.parse(caseData.ai_summary)
    : caseData.ai_summary || {};

const clinicalNotes = summary.clinical_notes || [];

console.log("CASE ID:", caseId);
console.log("CASE DATA:", caseData);
console.log("SUMMARY:", summary);
console.log("CLINICAL NOTES:", clinicalNotes);

  const imageFiles = caseFiles.filter(
    (file) => file.file_type === "image"
  );

  const labFiles = caseFiles.filter(
    (file) => file.file_type === "lab_report"
  );

  const videoFiles = caseFiles.filter(
    (file) => file.file_type === "video"
  );

  return (
    <section className="casePage">
      <div className="caseTop">
        <button className="backBtn" onClick={navigateHome}>
          <FaArrowLeft />
          Back to Cases
        </button>

        <div>
          <p>{caseData.status} Clinical Case</p>
          <h1>{caseData.case_title}</h1>
        </div>
      </div>

      <div className="caseLayout">
        <aside className="caseSideMenu">
          {caseSections.map((section) => (
            <button
              key={section.name}
              className={
                activeSection === section.name
                  ? "sectionBtn active"
                  : "sectionBtn"
              }
              onClick={() => setActiveSection(section.name)}
            >
              <span className="iconWrap">
                {section.icon}
              </span>
              {section.name}
            </button>
          ))}
        </aside>

        <section className="caseSummaryPanel">
          <h2>{activeSection}</h2>

<StructuredClinicalSummary summary={summary} />


          {activeSection === "AI Clinical Interpretation" && (
            <StructuredClinicalSummary summary={summary} />
          )}

          {activeSection === "Lab Reports" && (
            labFiles.length > 0 ? (
              <div className="labTableWrap">
                {labFiles.map((file) => (
                  <div key={file.id} className="labReportCard">
                    <h3>{cleanFileName(file.original_name) || "Lab Report"}</h3>

                    {file.ai_analysis?.tests?.length ? (
                      <table className="notesTable">
                        <thead>
                          <tr>
                            <th>Test Name</th>
                            <th>Value</th>
                            <th>Normal Range</th>
                            <th>Status</th>
                            <th>Interpretation</th>
                          </tr>
                        </thead>

                        <tbody>
                          {file.ai_analysis.tests.map((test, index) => (
                            <tr key={index}>
                              <td>{test.test_name || "Not mentioned"}</td>
                              <td>{test.value || "Not mentioned"}</td>
                              <td>{test.normal_range || "Not mentioned"}</td>
                              <td>{test.status || "Not mentioned"}</td>
                              <td>{test.interpretation || "Not mentioned"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : (
                      <>
                        <p>No structured lab analysis available.</p>

                        <a
                          className="fileLink"
                          href={`${API_BASE_URL}/storage/${file.filename}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open uploaded lab file
                        </a>
                      </>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p>No lab reports uploaded.</p>
            )
          )}

          {activeSection === "Image" && (
            imageFiles.length > 0 ? (
              <div className="imageGallery">
                {imageFiles.map((file) => (
                  <a
                    key={file.id}
                    href={`${API_BASE_URL}/storage/${file.filename}`}
                    target="_blank"
                    rel="noreferrer"
                    className="imageCard"
                  >
                    <img
                      className="caseImageThumb"
                      src={`${API_BASE_URL}/storage/${file.filename}`}
                      alt={file.original_name || "Case image"}
                    />

                    <p>{file.original_name || "Case Image"}</p>
                  </a>
                ))}
              </div>
            ) : (
              <p>No images uploaded for this case.</p>
            )
          )}

          {activeSection === "Videos" && (
            videoFiles.length > 0 ? (
              <div className="videoGrid">
                {videoFiles.map((file) => (
                  <video
                    key={file.id}
                    className="caseVideo"
                    controls
                    src={`${API_BASE_URL}/storage/${file.filename}`}
                  />
                ))}
              </div>
            ) : (
              <p>No videos uploaded.</p>
            )
          )}

          {activeSection === "Patient Clinical Progress Notes" && (
            clinicalNotes.length > 0 ? (
              <div className="notesTableWrap">
                <table className="notesTable">
                  <thead>
                    <tr>
                      <th>Day</th>
                      <th>Progress</th>
                      <th>Medication</th>
                      <th>Vitals</th>
                    </tr>
                  </thead>

                  <tbody>
                    {clinicalNotes.map((note, index) => (
                      <tr key={index}>
                        <td>{note.day || "N/A"}</td>
                        <td>{note.progress || "N/A"}</td>
                        <td>{note.medication || "N/A"}</td>
                        <td>{note.vitals || "N/A"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p>No clinical notes available.</p>
            )
          )}

          {activeSection === "Flow Chart" && (
            summary.flowchart?.length ? (
              <div className="graphFlowWrap">
                {summary.flowchart.map((item, index) => (
                  <div key={index} className="graphFlowItem">
                    <div className="graphFlowNode">
                      <div className="graphFlowIcon">
                        {getFlowIcon(item.type)}
                      </div>

                      <h3>{item.step || `Step ${index + 1}`}</h3>

                      <p>{item.description || "No description available."}</p>

                      <span className="flowType">
                        {item.type || "clinical step"}
                      </span>
                    </div>

                    {index < summary.flowchart.length - 1 && (
                      <div className="graphFlowConnector">
                        <div className="graphFlowLine" />
                        <div className="graphFlowArrowHead" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p>No graphical flowchart generated yet.</p>
            )
          )}

          {activeSection === "Q-Hub" && (
            <div className="keywordWrap">
              {summary.keywords?.length ? (
                summary.keywords.map((item) => (
                  <span key={item}>
                    {String(item).replace("-", "").trim()}
                  </span>
                ))
              ) : (
                <p>No keywords available.</p>
              )}
            </div>
          )}

          {activeSection === "Clinical Impression & Conclusion" && (
            <p>{summary.conclusion || "Not mentioned"}</p>
          )}
        </section>
      </div>
    </section>
  );
}
