from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.db.database import Base, engine

from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.api.ai_summary import router as ai_summary_router
from app.api.ocr import router as ocr_router
from app.api.process_case import router as process_router
from app.api.cases import router as cases_router
from app.api.full_process import router as full_process_router
from app.api.case_files import router as case_files_router
from app.api.rag import router as rag_router
from app.api.case_ai_edit import router as case_ai_edit_router
from app.api.flowchart_ai import router as flowchart_ai_router

from app.models.case_model import Case
from app.models.case_file_model import CaseFile

app = FastAPI(
    title="CCL Intelligence API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ccl.doctutorials.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

STORAGE_DIR = Path("storage")
STORAGE_DIR.mkdir(exist_ok=True)

app.mount(
    "/storage",
    StaticFiles(directory="storage"),
    name="storage"
)

@app.get("/")
def root():
    return {
        "message": "CCL Intelligence API is running"
    }

app.include_router(health_router)
app.include_router(upload_router)
app.include_router(ai_summary_router)
app.include_router(ocr_router)
app.include_router(process_router)
app.include_router(cases_router)
app.include_router(full_process_router)
app.include_router(case_files_router)
app.include_router(rag_router)
app.include_router(case_ai_edit_router)
app.include_router(flowchart_ai_router)
