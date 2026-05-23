import { useEffect, useMemo, useState } from "react";
import api from "../services/api";

export default function LibraryPage({ navigateToCase }) {
  const [cases, setCases] = useState([]);
  const [search, setSearch] = useState("");

  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedSpeciality, setSelectedSpeciality] = useState("");
  const [selectedDisease, setSelectedDisease] = useState("");

  async function loadCases() {
    try {
      const response = await api.get(`/cases/published?t=${Date.now()}`);
      setCases(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error("Failed to load published cases", error);
    }
  }

  useEffect(() => {
    loadCases();
  }, []);

  const filteredCases = useMemo(() => {
    const q = search.trim().toLowerCase();

    if (!q) return cases;

    return cases.filter((item) =>
      [
        item.case_title,
        item.subject,
        item.speciality,
        item.super_speciality,
        item.disease
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q)
    );
  }, [cases, search]);

  const subjects = useMemo(() => {
    return [...new Set(filteredCases.map((item) => item.subject).filter(Boolean))];
  }, [filteredCases]);

  const specialities = useMemo(() => {
    if (!selectedSubject) return [];

    return [
      ...new Set(
        filteredCases
          .filter((item) => item.subject === selectedSubject)
          .map((item) => item.super_speciality || item.speciality)
          .filter(Boolean)
      )
    ];
  }, [filteredCases, selectedSubject]);

  const diseases = useMemo(() => {
    if (!selectedSubject || !selectedSpeciality) return [];

    return [
      ...new Set(
        filteredCases
          .filter(
            (item) =>
              item.subject === selectedSubject &&
              (item.super_speciality || item.speciality) === selectedSpeciality
          )
          .map((item) => item.disease)
          .filter(Boolean)
      )
    ];
  }, [filteredCases, selectedSubject, selectedSpeciality]);

  const finalCases = useMemo(() => {
    if (!selectedSubject || !selectedSpeciality || !selectedDisease) return [];

    return filteredCases.filter(
      (item) =>
        item.subject === selectedSubject &&
        (item.super_speciality || item.speciality) === selectedSpeciality &&
        item.disease === selectedDisease
    );
  }, [filteredCases, selectedSubject, selectedSpeciality, selectedDisease]);

  function selectSubject(subject) {
    if (selectedSubject === subject) {
      setSelectedSubject("");
      setSelectedSpeciality("");
      setSelectedDisease("");
      return;
    }

    setSelectedSubject(subject);
    setSelectedSpeciality("");
    setSelectedDisease("");
  }


  useEffect(() => {
    requestAnimationFrame(() => {
      const activeSubject = document.querySelector(".subjectColumn .libraryNode.active");
      const activeSpeciality = document.querySelectorAll(".flowColumn")[1]?.querySelector(".libraryNode.active");
      const activeDisease = document.querySelectorAll(".flowColumn")[2]?.querySelector(".libraryNode.active");

      if (activeSubject) {
        document.documentElement.style.setProperty(
          "--subject-align",
          `${activeSubject.offsetTop}px`
        );
      }

      if (activeSpeciality) {
        document.documentElement.style.setProperty(
          "--speciality-align",
          `${activeSpeciality.offsetTop}px`
        );
      }

      if (activeDisease) {
        document.documentElement.style.setProperty(
          "--disease-align",
          `${activeDisease.offsetTop}px`
        );
      }
    });
  }, [selectedSubject, selectedSpeciality, selectedDisease]);


  function selectSpeciality(speciality) {
    if (selectedSpeciality === speciality) {
      setSelectedSpeciality("");
      setSelectedDisease("");
      return;
    }

    setSelectedSpeciality(speciality);
    setSelectedDisease("");
  }

  return (
    <div className="libraryPage">
      <header className="libraryHero">
        <div className="libraryLogoBox">
          <img src="/logo.png" alt="DocTutorials" />
        </div>

        <div>
          <h1>Clinical Case Library</h1>
          <p>Explore cases by Subject → Super Speciality → Disease → Case.</p>
        </div>

        <button className="refreshBtn" onClick={loadCases}>
          Refresh
        </button>
      </header>

      <div className="librarySearchBox">
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search case by title, subject, speciality, disease..."
        />
      </div>

      <section
        className={
          selectedSubject
            ? "dynamicLibraryFlow activeFlow"
            : "dynamicLibraryFlow initialSubjectFlow"
        }
      >
        <div className="flowColumn subjectColumn">
          <h2>Subjects</h2>

          {subjects.length === 0 ? (
            <div className="emptyLibraryState">No published subjects found.</div>
          ) : (
            subjects.map((subject) => (
              <button
                type="button"
                key={subject}
                className={selectedSubject === subject ? "libraryNode active" : "libraryNode"}
                onClick={() => selectSubject(subject)}
              >
                <span className="libraryIcon">🧪</span>

                <div>
                  <strong>{subject}</strong>
                  <span>Medical Subject</span>
                </div>
              </button>
            ))
          )}
        </div>

        {selectedSubject && (
          <div className="flowColumn">
            <h2>Super Specialities</h2>

            {specialities.map((speciality) => (
              <button
                type="button"
                key={speciality}
                className={
                  selectedSpeciality === speciality ? "libraryNode active" : "libraryNode"
                }
                onClick={() => selectSpeciality(speciality)}
              >
                <span className="libraryIcon">🩺</span>

                <div>
                  <strong>{speciality}</strong>
                  <span>Super Speciality</span>
                </div>
              </button>
            ))}
          </div>
        )}

        {selectedSpeciality && (
          <div className="flowColumn">
            <h2>Diseases</h2>

            {diseases.map((disease) => (
              <button
                type="button"
                key={disease}
                className={selectedDisease === disease ? "libraryNode active" : "libraryNode"}
                onClick={() => setSelectedDisease(disease)}
              >
                <span className="libraryIcon">🧠</span>

                <div>
                  <strong>{disease}</strong>
                  <span>Disease Category</span>
                </div>
              </button>
            ))}
          </div>
        )}

        {selectedDisease && (
          <div className="flowColumn">
            <h2>Cases</h2>

            {finalCases.map((item) => (
              <button
                type="button"
                key={item.id}
                className="libraryCaseCard"
                onClick={() => navigateToCase(item.id)}
              >
                <span className="libraryIcon">🧾</span>

                <div>
                  <strong>{item.case_title}</strong>
                  <span>Clinical Case</span>
                </div>

                <small>Case #{item.id}</small>
              </button>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
