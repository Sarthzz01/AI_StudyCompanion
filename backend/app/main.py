import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, SessionLocal, run_migrations
import app.models  # Ensures all 16 models are registered
from app.seed import seed_database
from app.routers import auth, profile, subjects, materials, ai, tutor, summaries, flashcards, quizzes, progress, recommendations, study_plan, revision, viva, instructor, notifications, notes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    
    # Run seed script if database is fresh
    db = SessionLocal()
    try:
        seed_database(db)
        from app.seed import seed_phase3_chunks, seed_phase9_instructor_data, seed_notes_data
        seed_phase3_chunks(db)
        seed_phase9_instructor_data(db)
        seed_notes_data(db)
    finally:
        db.close()
        
    yield
    logger.info("Shutting down AI Study Companion API...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Backend API and Database Foundation for AI Study Companion — Phase 9 (Instructor Module & Assessment Management)",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers under /api
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
app.include_router(subjects.router, prefix=settings.API_V1_STR)
app.include_router(materials.router, prefix=settings.API_V1_STR)
app.include_router(tutor.router, prefix=settings.API_V1_STR)
app.include_router(summaries.router, prefix=settings.API_V1_STR)
app.include_router(flashcards.router, prefix=settings.API_V1_STR)
app.include_router(quizzes.router)
app.include_router(progress.router, prefix=settings.API_V1_STR)
app.include_router(recommendations.router)
app.include_router(study_plan.router)
app.include_router(revision.router)
app.include_router(viva.router)
app.include_router(instructor.router, prefix=settings.API_V1_STR)
app.include_router(instructor.student_assessments_router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)
app.include_router(notes.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "api": settings.API_V1_STR
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
