import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import {
  FaArrowLeft,
  FaCheckCircle,
  FaFileMedical,
  FaHeartbeat,
  FaHospital,
  FaNotesMedical,
  FaProjectDiagram,
  FaQuestionCircle,
  FaVideo
} from "react-icons/fa";

import api from "../services/api";
import { getCaseFiles } from "../services/caseService";
import StructuredClinicalSummary from "../components/StructuredClinicalSummary";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";

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

function cleanFileName(name = "") {
  return name.replace(/\.[^/.]+$/, "");
}

function getSummary(caseData) {
  if (!caseData?.ai_summary) return {};

  if (typeof caseData.ai_summary === "string") {
    try {
      return JSON.parse(caseData.ai_summary);
    } catch {
      return {};
    }
  }

  return caseData.ai_summary;
}

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

function SimpleClinicalCard({ title, text }) {
  return (
    <article className="smartClinicalCard">
      <h3>{title}</h3>
      <p>{text || "Not clearly mentioned."}</p>
    </article>
  );
}

export default function CasePage({ navigateHome }) {
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
      setCaseFiles(Array.isArray(filesResponse) ? filesResponse : []);
    } catch (error) {
      console.error("Failed to load case", error);
      alert("Failed to load case");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCase();
  }, [caseId]);

  if (loading) return <p className="pageState">Loading case...</p>;
  if (!caseData) return <p className="pageState">Case not found.</p>;

  const summary = getSummary(caseData);
  const clinicalNotes = Array.isArray(summary.clinical_notes) ? summary.clinical_notes : [];

  const imageFiles = caseFiles.filter((file) => file.file_type === "image");
  const labFiles = caseFiles.filter((file) => file.file_type === "lab_report");
  const videoFiles = caseFiles.filter((file) => file.file_type === "video");

  return (
    <div className="casePage">
      <header className="caseTop">
        <button className="backBtn" onClick={navigateHome}>
          <FaArrowLeft />
          Back to Cases
        </button>

        <div>
          <p>{caseData.status} Clinical Case</p>
          <h1>{caseData.case_title}</h1>
        </div>
      </header>

      <section className="caseLayout">
        <nav className="caseSideMenu" aria-label="Case sections">
          {caseSections.map((section) => (
            <button
              type="button"
              key={section.name}
              className={activeSection === section.name ? "sectionBtn active" : "sectionBtn"}
              onClick={() => setActiveSection(section.name)}
            >
              <span className="iconWrap">{section.icon}</span>
              <span>{section.name}</span>
            </button>
          ))}
        </nav>

        <main className="caseSummaryPanel">
          <h2>{activeSection}</h2>

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
                      <a
                        className="fileLink"
                        href={`${API_BASE_URL}/storage/${file.filename}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open uploaded lab file
                      </a>
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

                    <p>{cleanFileName(file.original_name) || "Case Image"}</p>
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
                      <div className="graphFlowIcon">{getFlowIcon(item.type)}</div>
                      <h3>{item.step || `Step ${index + 1}`}</h3>
                      <p>{item.description || "No description available."}</p>
                      <span className="flowType">{item.type || "clinical step"}</span>
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
            <div className="qhubGrid">
              {summary.qhub_questions?.length ? (
                summary.qhub_questions.map((item, index) => (
                  <div className="qhubCard" key={index}>
                    <div className="qhubType">{item.type || "Clinical"}</div>
                    <div className="qhubQuestion">{item.question}</div>
                  </div>
                ))
              ) : (
                <p>No AI-generated questions available.</p>
              )}
            </div>
          )}

          {activeSection === "Clinical Impression & Conclusion" && (
            <SimpleClinicalCard
              title="Clinical Impression & Conclusion"
              text={summary.conclusion}
            />
          )}
        </main>
      </section>
    </div>
  );
}
