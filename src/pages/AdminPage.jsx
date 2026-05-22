import { useState } from "react";

import UploadSection from "../sections/admin/UploadSection";
import DashboardSection from "../sections/admin/DashboardSection";
import EditSection from "../sections/admin/EditSection";

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState("upload");
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);

  function openSection(section) {
    setActiveTab(section);
    setMenuOpen(false);
  }

  return (
    <section className="adminLayout">
      <button
        className="mobileMenuBtn"
        onClick={() => setMenuOpen(!menuOpen)}
      >
        ☰ CCL Intelligence
      </button>

      <aside className={menuOpen ? "adminSidebar open" : "adminSidebar"}>
        <div className="adminBrand">
          <img src="/logo.png" alt="DocTutorials" />
          <h2>CCL Intelligence</h2>
        </div>

        <button
          className={activeTab === "upload" ? "sidebarBtn active" : "sidebarBtn"}
          onClick={() => openSection("upload")}
        >
          Upload Case
        </button>

        <button
          className={activeTab === "dashboard" ? "sidebarBtn active" : "sidebarBtn"}
          onClick={() => openSection("dashboard")}
        >
          Manage Uploads
        </button>

        <button
          className={activeTab === "edit" ? "sidebarBtn active" : "sidebarBtn"}
          onClick={() => openSection("edit")}
        >
          Edit & Publish
        </button>
      </aside>

      {menuOpen && (
        <div
          className="mobileOverlay"
          onClick={() => setMenuOpen(false)}
        />
      )}

      <main className="adminMainContent">
        {activeTab === "upload" && <UploadSection />}

        {activeTab === "dashboard" && (
          <DashboardSection
            setSelectedCaseId={setSelectedCaseId}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === "edit" && (
          <EditSection selectedCaseId={selectedCaseId} />
        )}
      </main>
    </section>
  );
}
