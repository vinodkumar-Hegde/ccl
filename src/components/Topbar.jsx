export default function Topbar() {

  return (
    <header className="topbar searchOnlyTopbar">

      <div className="searchBox">

        <span>🔍</span>

        <input
          type="text"
          placeholder="
          Search subjects,
          diseases,
          cases..."
        />

      </div>

    </header>
  );
}