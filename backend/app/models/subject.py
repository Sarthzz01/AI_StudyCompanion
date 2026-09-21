from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=True, index=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    topics = relationship("Topic", back_populates="subject", cascade="all, delete-orphan")
    materials = relationship("Material", back_populates="subject")

class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0, nullable=False)
    difficulty_level = Column(String(50), default="medium", nullable=False)  # easy, medium, hard
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    subject = relationship("Subject", back_populates="topics")
    questions = relationship("Question", back_populates="topic", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="topic", cascade="all, delete-orphan")
    learner_models = relationship("LearnerModel", back_populates="topic_rel", cascade="all, delete-orphan")
