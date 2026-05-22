import { useEffect, useMemo, useState } from "react";

import { getCases } from "../../services/caseService";

export default function DashboardSection({
  setSelectedCaseId,
  setActiveTab
}) {
  const [cases, setCases] = useState([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [processingFilter, setProcessingFilter] = useState("all");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadCases();
  }, []);

  async function loadCases() {
    setLoading(true);

    try {
      const data = await getCases();

      console.log("FETCHED CASES:", data);

      if (Array.isArray(data)) {
        setCases(data);
      } else {
        setCases([]);
      }
    } catch (error) {
      console.error("Failed to fetch cases:", error);
      alert("Failed to fetch cases. Check backend /cases/ endpoint.");
    } finally {
      setLoading(false);
    }
  }

  const filteredCases = useMemo(() => {
    const query = search.trim().toLowerCase();

    return cases.filter((item) => {
      const searchableText = [
        item.id,
        item.case_title,
        item.subject,
        item.speciality,
        item.disease,
        item.status,
        item.processing_status
      ]
        .map((value) =>
          String(value || "").toLowerCase()
        )
        .join(" ");

      const matchesSearch =
        query === "" ||
        searchableText.includes(query);

      const matchesStatus =
        statusFilter === "all" ||
        item.status === statusFilter;

      const matchesProcessing =
        processingFilter === "all" ||
        item.processing_status === processingFilter;

      return (
        matchesSearch &&
        matchesStatus &&
        matchesProcessing
      );
    });
  }, [
    cases,
    search,
    statusFilter,
    processingFilter
  ]);

  function statusChip(status) {
    if (status === "published") {
      return "chip chipGreen";
    }

    return "chip chipOrange";
  }

  function processingChip(status) {
    if (status === "completed") {
      return "chip chipGreen";
    }

    if (status === "processing") {
      return "chip chipBlue";
    }

    if (status === "queued") {
      return "chip chipPurple";
    }

    if (status === "failed") {
      return "chip chipRed";
    }

    return "chip chipGray";
  }

  return (
    <div className="adminCard">
      <div className="dashboardTop">
        <div>
          <h1>Uploads Dashboard</h1>
          <p>
            Search, filter, edit and publish all uploaded clinical cases.
          </p>
        </div>

        <button
          className="modernRefreshBtn"
          onClick={loadCases}
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      <div className="modernSearchBar">
        <input
          type="text"
          value={search}
          placeholder="Search by ID, title, subject, speciality, disease..."
          onChange={(e) =>
            setSearch(e.target.value)
          }
        />

        <select
          value={statusFilter}
          onChange={(e) =>
            setStatusFilter(e.target.value)
          }
        >
          <option value="all">All Publish Status</option>
          <option value="draft">Draft</option>
          <option value="published">Published</option>
        </select>

        <select
          value={processingFilter}
          onChange={(e) =>
            setProcessingFilter(e.target.value)
          }
        >
          <option value="all">All AI Status</option>
          <option value="queued">Queued</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="pending">Pending</option>
        </select>
      </div>

      <p className="resultMeta">
        Showing {filteredCases.length} of {cases.length} cases
      </p>

      <div className="tableWrap">
        <table className="adminTable modernTable">
          <thead>
            <tr>
              <th>ID</th>
              <th>Case Title</th>
              <th>Subject</th>
              <th>Speciality</th>
              <th>Disease</th>
              <th>Publish Status</th>
              <th>AI Status</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {filteredCases.map((item) => (
              <tr key={item.id}>
                <td>#{item.id}</td>

                <td>
                  <strong>
                    {item.case_title}
                  </strong>
                </td>

                <td>{item.subject}</td>

                <td>{item.speciality}</td>

                <td>{item.disease}</td>

                <td>
                  <span className={statusChip(item.status)}>
                    {item.status}
                  </span>
                </td>

                <td>
                  <span
                    className={processingChip(
                      item.processing_status
                    )}
                  >
                    {item.processing_status || "N/A"}
                  </span>
                </td>

                <td>
                  <button
                    className="modernEditBtn"
                    
                    onClick={() => {
                      setSelectedCaseId(item.id);
                      setActiveTab("edit");
                    }}
                  >
                    Edit
                  </button>
                </td>
              </tr>
            ))}

            {!filteredCases.length && (
              <tr>
                <td
                  colSpan="8"
                  className="emptyTable"
                >
                  No matching cases found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
