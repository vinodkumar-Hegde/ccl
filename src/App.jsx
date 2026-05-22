import { useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";

import LibraryPage from "./pages/LibraryPage";
import AdminPage from "./pages/AdminPage";
import CasePage from "./pages/CasePage";

export default function App() {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  function goTo(path) {
    navigate(path);
    setMenuOpen(false);
  }

  function navigateToCase(caseId) {
    navigate(`/case/${caseId}`);
    setMenuOpen(false);
  }

  return (
    <div className="appShell">
      <button
        className="globalMenuBtn"
        onClick={() => setMenuOpen(true)}
      >
        ☰ CCL Intelligence
      </button>

      <aside className={menuOpen ? "mainSidebar open" : "mainSidebar"}>
        <h1>CCL Intelligence</h1>

        <button onClick={() => goTo("/")}>
          User Library
        </button>

        <button onClick={() => goTo("/admin")}>
          Admin Panel
        </button>
      </aside>

      {menuOpen && (
        <div
          className="mainOverlay"
          onClick={() => setMenuOpen(false)}
        />
      )}

      <main className="appContent">
        <Routes>
          <Route
            path="/"
            element={
              <LibraryPage navigateToCase={navigateToCase} />
            }
          />

          <Route
            path="/admin"
            element={<AdminPage />}
          />

          <Route
            path="/case/:caseId"
            element={
              <CasePage navigateHome={() => goTo("/")} />
            }
          />
        </Routes>
      </main>
    </div>
  );
}
