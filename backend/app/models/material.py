from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Material(Base):
    __tablename__ = "materials"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    type = Column(String(50), default="PDF", nullable=False)  # PDF, Notes, Slides, Video
    pages = Column(Integer, default=0, nullable=False)
    topics_count = Column(Integer, default=0, nullable=False)
    last_studied = Column(String(100), default="Just now", nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    color = Column(String(50), default="brand", nullable=False)
    description = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)
    raw_filename = Column(String(255), nullable=True)
    processing_status = Column(String(50), default="ready", nullable=False)  # ready, processing, failed
    content_text = Column(Text, nullable=True)
    topics_json = Column(JSON, default=list, nullable=False)  # [{ name: '...', progress: 0 }]
    recent_activity_json = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="materials")
    subject = relationship("Subject", back_populates="materials")
    chunks = relationship("DocumentChunk", back_populates="material", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="material", cascade="all, delete-orphan")
    tutor_interactions = relationship("TutorInteraction", back_populates="material", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="material", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="material", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="material", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="material", cascade="all, delete-orphan")
