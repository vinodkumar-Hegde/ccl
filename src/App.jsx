import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import { useState } from "react";

import Sidebar from "./components/Sidebar";
import LibraryPage from "./pages/LibraryPage";
import AdminPage from "./pages/AdminPage";
import CasePage from "./pages/CasePage";

function AppLayout() {
  const navigate = useNavigate();

  const [view, setView] = useState("user");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  function navigateToCase(caseId) {
    navigate(`/case/${caseId}`);
  }

  function navigateHome() {
    navigate("/");
  }

  return (
    <main className="app">
      <Sidebar
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        setView={setView}
        navigate={navigate}
      />

      <section className="content">
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
            element={<CasePage navigateHome={navigateHome} />}
          />

          <Route
            path="*"
            element={<LibraryPage navigateToCase={navigateToCase} />}
          />
        </Routes>
      </section>
    </main>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}