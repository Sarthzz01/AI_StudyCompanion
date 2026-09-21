import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Study Companion"
    API_V1_STR: str = "/api"
    JWT_SECRET: str = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "super-secret-jwt-key-for-ai-study-companion-phase-2-2026"))
    SECRET_KEY: str = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "super-secret-jwt-key-for-ai-study-companion-phase-2-2026"))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database config: default to PostgreSQL, with graceful fallback to SQLite if PostgreSQL is unreachable
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_study_companion"
    )
    SQLITE_FALLBACK_URL: str = "sqlite:///./ai_study_companion.db"
    
    # CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # Gemini AI Configuration (Server-Side Only)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    
    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        extra = "allow"

settings = Settings()
