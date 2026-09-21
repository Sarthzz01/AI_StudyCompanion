import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger("uvicorn.error")

Base = declarative_base()

def get_engine():
    db_url = settings.DATABASE_URL
    try:
        if db_url.startswith("sqlite"):
            engine = create_engine(db_url, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(db_url, pool_pre_ping=True)
            # Test connection
            with engine.connect() as conn:
                pass
            logger.info(f"Connected successfully to primary database: {db_url.split('@')[-1]}")
            return engine
    except Exception as e:
        logger.warning(f"Could not connect to primary database ({e}). Falling back to SQLite database at {settings.SQLITE_FALLBACK_URL}")
        engine = create_engine(settings.SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})
    return engine

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
