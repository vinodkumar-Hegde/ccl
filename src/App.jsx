import { useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";

import LibraryPage from "./pages/LibraryPage";
import AdminPage from "./pages/AdminPage";
import CasePage from "./pages/CasePage";

import logo from "./assets/doctutorials-logo.png";

export default function App() {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  function goTo(path) {
    navigate(path);
    setSidebarOpen(false);
  }

  function navigateToCase(caseId) {
    navigate(`/case/${caseId}`);
    setSidebarOpen(false);
  }

  return (
    <div className="appRoot">
      <button
        className="sidebarToggle"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        ☰
      </button>

      {sidebarOpen && (
        <>
          <div
            className="sidebarBackdrop"
            onClick={() => setSidebarOpen(false)}
          />

          <aside className="globalSidebar">
            <div className="sidebarBrand">
              <img src={logo} alt="DocTutorials Logo" />
              <h1>CCL Intelligence</h1>
            </div>

            <button onClick={() => goTo("/")}>User Library</button>
            <button onClick={() => goTo("/admin")}>Admin Panel</button>
          </aside>
        </>
      )}

      <main className="mainWorkspace">
        <Routes>
          <Route
            path="/"
            element={<LibraryPage navigateToCase={navigateToCase} />}
          />

          <Route
            path="/admin"
            element={<AdminPage />}
          />

          <Route
            path="/case/:caseId"
            element={<CasePage navigateHome={() => goTo("/")} />}
          />
        </Routes>
      </main>
    </div>
  );
}
