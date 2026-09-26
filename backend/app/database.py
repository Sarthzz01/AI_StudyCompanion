import logging
from sqlalchemy import create_engine, text
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

def run_migrations(target_engine=None):
    eng = target_engine or engine
    try:
        with eng.connect() as conn:
            # Check revision_schedules columns in SQLite
            res = conn.execute(text("PRAGMA table_info(revision_schedules)")).fetchall()
            existing_cols = {row[1] for row in res}
            if existing_cols:
                if "topic_name" not in existing_cols:
                    conn.execute(text("ALTER TABLE revision_schedules ADD COLUMN topic_name VARCHAR(200)"))
                if "material_id" not in existing_cols:
                    conn.execute(text("ALTER TABLE revision_schedules ADD COLUMN material_id VARCHAR(100)"))
                if "repetition_count" not in existing_cols:
                    conn.execute(text("ALTER TABLE revision_schedules ADD COLUMN repetition_count INTEGER DEFAULT 1"))
                if "last_reviewed" not in existing_cols:
                    conn.execute(text("ALTER TABLE revision_schedules ADD COLUMN last_reviewed DATETIME"))
                if "updated_at" not in existing_cols:
                    conn.execute(text("ALTER TABLE revision_schedules ADD COLUMN updated_at DATETIME"))
                conn.commit()

            # Check tutor_interactions columns in SQLite
            res_tutor = conn.execute(text("PRAGMA table_info(tutor_interactions)")).fetchall()
            existing_tutor_cols = {row[1] for row in res_tutor}
            if existing_tutor_cols:
                if "conversation_id" not in existing_tutor_cols:
                    conn.execute(text("ALTER TABLE tutor_interactions ADD COLUMN conversation_id VARCHAR(100)"))
                if "title" not in existing_tutor_cols:
                    conn.execute(text("ALTER TABLE tutor_interactions ADD COLUMN title VARCHAR(255)"))
                conn.commit()
    except Exception as e:
        logger.warning(f"Migration check error: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
