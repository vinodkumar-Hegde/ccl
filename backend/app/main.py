from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.models.case_file_model import CaseFile
from app.db.database import Base, engine
from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.api.ai_summary import router as ai_summary_router
from app.api.ocr import router as ocr_router
from app.api.process_case import router as process_router
from app.api.cases import router as cases_router
from app.api.full_process import router as full_process_router
from app.models.case_model import Case
from app.api.case_files import router as case_files_router
from app.api.rag import router as rag_router
from app.api.case_ai_edit import router as case_ai_edit_router

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="CCL Intelligence API",
    version="1.0.0",
    description="AI RAG based Clinical Case Library Backend"
)

app.mount(
    "/storage",
    StaticFiles(directory="storage"),
    name="storage"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
def root():
    return {
        "message": "CCL Backend API is running"
    }