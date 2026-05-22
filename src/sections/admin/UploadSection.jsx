import { useState } from "react";

import { fullProcessCase } from "../../services/caseService";

export default function UploadSection() {
  const [form, setForm] = useState({
    subject: "",
    speciality: "",
    disease: "",
    case_title: ""
  });

  const [caseSheet, setCaseSheet] = useState(null);
  const [labReports, setLabReports] = useState([]);
  const [images, setImages] = useState([]);
  const [videos, setVideos] = useState([]);

  const [loading, setLoading] = useState(false);
  const [createdCase, setCreatedCase] = useState(null);
  const [message, setMessage] = useState("");

  function updateForm(e) {
    setForm({
      ...form,
      [e.target.name]: e.target.value
    });
  }

  async function handleUpload(e) {
    e.preventDefault();

    if (!caseSheet) {
      alert("Please upload case sheet");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const data = new FormData();

      data.append("subject", form.subject);
      data.append("speciality", form.speciality);
      data.append("disease", form.disease);
      data.append("case_title", form.case_title);
      data.append("case_sheet", caseSheet);

      labReports.forEach((file) => {
        data.append("lab_reports", file);
      });

      images.forEach((file) => {
        data.append("images", file);
      });

      videos.forEach((file) => {
        data.append("videos", file);
      });

      const response = await fullProcessCase(data);

      console.log("UPLOAD RESPONSE:", response);

      setCreatedCase(response);

      setMessage(
        `Uploaded successfully. Case ID: ${response.case_id}. AI Status: ${response.processing_status}`
      );

      alert("Case uploaded successfully. AI processing started.");
    } catch (error) {
      console.error("UPLOAD ERROR:", error);

      const backendMessage =
        error?.response?.data?.detail ||
        error?.message ||
        "Unknown upload error";

      setMessage(`Upload failed: ${backendMessage}`);

      alert(`Upload failed: ${backendMessage}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="adminCard">
      <h1>Upload Clinical Case</h1>

      <form onSubmit={handleUpload} className="adminForm">
        <input
          name="subject"
          placeholder="Subject"
          value={form.subject}
          onChange={updateForm}
          required
        />

        <input
          name="speciality"
          placeholder="Super Speciality"
          value={form.speciality}
          onChange={updateForm}
          required
        />

        <input
          name="disease"
          placeholder="Disease"
          value={form.disease}
          onChange={updateForm}
          required
        />

        <input
          name="case_title"
          placeholder="Case Title"
          value={form.case_title}
          onChange={updateForm}
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
          onChange={(e) =>
            setLabReports(Array.from(e.target.files))
          }
        />

        <label>Clinical Images</label>
        <input
          type="file"
          accept=".jpg,.jpeg,.png"
          multiple
          onChange={(e) =>
            setImages(Array.from(e.target.files))
          }
        />

        <label>Clinical Videos</label>
        <input
          type="file"
          accept=".mp4,.mov,.avi"
          multiple
          onChange={(e) =>
            setVideos(Array.from(e.target.files))
          }
        />

        <button type="submit" disabled={loading}>
          {loading ? "Uploading..." : "Upload + Start AI Processing"}
        </button>
      </form>

      {message && (
        <div className="uploadStatusBox">
          {message}
        </div>
      )}

      <div className="uploadPreview">
        <p>Case Sheet: {caseSheet ? caseSheet.name : "Not selected"}</p>
        <p>Lab Reports: {labReports.length}</p>
        <p>Images: {images.length}</p>
        <p>Videos: {videos.length}</p>

        {createdCase && (
          <>
            <p>Created Case ID: {createdCase.case_id}</p>
            <p>Processing Status: {createdCase.processing_status}</p>
          </>
        )}
      </div>
    </div>
  );
}
