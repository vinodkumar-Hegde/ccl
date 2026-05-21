import {
  FaBookMedical,
  FaUserMd,
  FaBars
} from "react-icons/fa";

export default function Sidebar({
  sidebarOpen,
  setSidebarOpen,
  navigate
}) {
  return (
    <aside className={sidebarOpen ? "sidebar open" : "sidebar"}>

      <div className="sidebarTop">

        <button
          className="menuBtn"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          <FaBars />
        </button>

        <h2>CCL Intelligence</h2>

      </div>

      <nav className="sidebarNav">

        <button onClick={() => navigate("/")}>
          <FaBookMedical />
          <span>User Library</span>
        </button>

        <button onClick={() => navigate("/admin")}>
          <FaUserMd />
          <span>Admin Panel</span>
        </button>

      </nav>

    </aside>
  );
}