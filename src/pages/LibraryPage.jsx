import { useEffect, useMemo, useState } from "react";
import { getPublishedCases } from "../services/caseService";

export default function LibraryPage({ navigateToCase }) {
  const [cases, setCases] = useState([]);
  const [search, setSearch] = useState("");

  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedSpeciality, setSelectedSpeciality] = useState(null);
  const [selectedDisease, setSelectedDisease] = useState(null);

  useEffect(() => {
    loadCases();
  }, []);

  async function loadCases() {
    const data = await getPublishedCases();
    setCases(Array.isArray(data) ? data : []);
  }

  const searchResults = useMemo(() => {
    const q = search.trim().toLowerCase();

    if (!q) return [];

    return cases.filter((item) => {
      const text = [
        item.id,
        item.case_title,
        item.subject,
        item.speciality,
        item.disease
      ]
        .map((v) => String(v || "").toLowerCase())
        .join(" ");

      return text.includes(q);
    });
  }, [cases, search]);

  const subjects = [
    ...new Set(cases.map((item) => item.subject).filter(Boolean))
  ].sort((a, b) => {
    if (a === selectedSubject) return -1;
    if (b === selectedSubject) return 1;
    return a.localeCompare(b);
  });

  const specialities = [
    ...new Set(
      cases
        .filter((item) => item.subject === selectedSubject)
        .map((item) => item.speciality)
        .filter(Boolean)
    )
  ].sort((a, b) => {
    if (a === selectedSpeciality) return -1;
    if (b === selectedSpeciality) return 1;
    return a.localeCompare(b);
  });

  const diseases = [
    ...new Set(
      cases
        .filter(
          (item) =>
            item.subject === selectedSubject &&
            item.speciality === selectedSpeciality
        )
        .map((item) => item.disease)
        .filter(Boolean)
    )
  ].sort((a, b) => {
    if (a === selectedDisease) return -1;
    if (b === selectedDisease) return 1;
    return a.localeCompare(b);
  });

  const finalCases = cases.filter(
    (item) =>
      item.subject === selectedSubject &&
      item.speciality === selectedSpeciality &&
      item.disease === selectedDisease
  );

  function resetBelow(level) {
    if (level === "subject") {
      setSelectedSpeciality(null);
      setSelectedDisease(null);
    }

    if (level === "speciality") {
      setSelectedDisease(null);
    }
  }

  return (
    <section className="libraryPage">
      <div className="libraryHero">

        <div className="libraryLogoWrap">

          <img
            src="/logo.png"
            alt="DocTutorials"
            className="libraryLogo"
          />

          <div>
            <h1>Clinical Case Library</h1>

            <p>
              Explore cases by Subject → Super Speciality → Disease → Case.
            </p>
          </div>

        </div>

        <button
          className="modernRefreshBtn"
          onClick={loadCases}
        >
          Refresh
        </button>

      </div>

      <div className="librarySearchBox">
        <input
          value={search}
          placeholder="Search case by title, subject, speciality, disease..."
          onChange={(e) => setSearch(e.target.value)}
        />

        {search && (
          <div className="searchResultPanel">
            {searchResults.length ? (
              searchResults.map((item) => (
                <button
                  key={item.id}
                  className="searchResultItem"
                  onClick={() => navigateToCase(item.id)}
                >
                  <strong><>
<div>
  <strong>{item.case_title}</strong>

  <span>
    {item.super_speciality || "Clinical Case"}
  </span>
</div>
</></strong>
                  <span>
                    {item.subject} → {item.speciality} → {item.disease}
                  </span>
                </button>
              ))
            ) : (
              <p>No matching cases found.</p>
            )}
          </div>
        )}
      </div>

      {!search && (
        <div className="dynamicLibraryFlow">
          <div
            className={`flowColumn ${
              selectedSubject ? "shiftLeft" : "centerStage"
            }`}
          >
            <h2>Subjects</h2>

            {subjects.map((subject) => (
              <button
                key=<>
<strong>{subject}</strong>
<span>Medical Subject</span>
</>
                className={
                  selectedSubject === subject
                    ? "libraryNode active"
                    : "libraryNode"
                }
                onClick={() => {
                  setSelectedSubject(subject);
                  resetBelow("subject");
                }}
              >
                <>
<strong>{subject}</strong>
<span>Medical Subject</span>
</>
              </button>
            ))}
          </div>

          {selectedSubject && (
            <div className="flowColumn animateSlide">
              <h2>Super Specialities</h2>

              {specialities.map((speciality) => (
                <button
                  key=<>
<strong>{speciality}</strong>
<span>Super Speciality</span>
</>
                  className={
                    selectedSpeciality === speciality
                      ? "libraryNode active"
                      : "libraryNode"
                  }
                  onClick={() => {
                    setSelectedSpeciality(speciality);
                    resetBelow("speciality");
                  }}
                >
                  <>
<strong>{speciality}</strong>
<span>Super Speciality</span>
</>
                </button>
              ))}
            </div>
          )}

          {selectedSpeciality && (
            <div className="flowColumn animateSlide">
              <h2>Diseases</h2>

              {diseases.map((disease) => (
                <button
                  key=<>
<strong>{disease}</strong>
<span>Disease Category</span>
</>
                  className={
                    selectedDisease === disease
                      ? "libraryNode active"
                      : "libraryNode"
                  }
                  onClick={() => setSelectedDisease(disease)}
                >
                  <>
<strong>{disease}</strong>
<span>Disease Category</span>
</>
                </button>
              ))}
            </div>
          )}

          {selectedDisease && (
            <div className="flowColumn animateSlide">
              <h2>Cases</h2>

              {finalCases.map((item) => (
                <button
                  key={item.id}
                  className="libraryCaseCard"
                  onClick={() => navigateToCase(item.id)}
                >
                  <strong><>
<div>
  <strong>{item.case_title}</strong>

  <span>
    {item.super_speciality || "Clinical Case"}
  </span>
</div>
</></strong>
                  <span>Case #{item.id}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
