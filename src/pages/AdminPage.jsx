import { useState } from "react";

import UploadSection from "../sections/admin/UploadSection";
import DashboardSection from "../sections/admin/DashboardSection";
import EditSection from "../sections/admin/EditSection";

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState("upload");

  const [selectedCaseId, setSelectedCaseId] = useState(null);

  return (
    <section className="adminLayout">
      <aside className="adminSidebar">
       <div className="sidebarLogoWrap">
  <img
    src="/logo.png"
    alt="DocTutorials"
    className="sidebarLogo"
  />

  <h2>CCL Admin</h2>
</div>

        <button
          className={
            activeTab === "upload"
              ? "sidebarBtn active"
              : "sidebarBtn"
          }
          onClick={() => setActiveTab("upload")}
        >
          Upload Case
        </button>

        <button
          className={
            activeTab === "dashboard"
              ? "sidebarBtn active"
              : "sidebarBtn"
          }
          onClick={() => setActiveTab("dashboard")}
        >
          Manage Uploads
        </button>

        <button
          className={
            activeTab === "edit"
              ? "sidebarBtn active"
              : "sidebarBtn"
          }
          onClick={() => setActiveTab("edit")}
        >
          Edit & Publish
        </button>
      </aside>

      <main className="adminMainContent">
        {activeTab === "upload" && (
          <UploadSection />
        )}

        {activeTab === "dashboard" && (
          <DashboardSection
            setSelectedCaseId={setSelectedCaseId}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === "edit" && (
          <EditSection
            selectedCaseId={selectedCaseId}
          />
        )}
      </main>
    </section>
  );
}
