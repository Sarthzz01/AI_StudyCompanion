from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class LearnerModel(Base):
    __tablename__ = "learner_models"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=True, index=True)
    topic = Column(String(200), nullable=False, index=True)  # Name of the topic
    mastery = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0%
    recall_reliability = Column(Float, default=0.5, nullable=False)  # 0.0 to 1.0 probability of recall
    quiz_accuracy = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0%
    flashcard_performance = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0%
    viva_performance = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0%
    difficulty = Column(String(50), default="medium", nullable=False)  # easy, medium, hard
    last_reviewed = Column(DateTime, nullable=True)
    next_review = Column(DateTime, nullable=True)
    recent_performance_json = Column(JSON, default=list, nullable=False)  # [{ "score": 85, "date": "..." }]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="learner_models")
    topic_rel = relationship("Topic", back_populates="learner_models")

class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    overall_accuracy = Column(Float, default=0.0, nullable=False)
    total_study_time_minutes = Column(Integer, default=0, nullable=False)
    questions_attempted = Column(Integer, default=0, nullable=False)
    quizzes_completed = Column(Integer, default=0, nullable=False)
    current_streak_days = Column(Integer, default=0, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False)
    history_json = Column(JSON, default=list, nullable=False)  # Accuracy over time, weekly stats, etc.

    user = relationship("User", back_populates="progress")

class RevisionSchedule(Base):
    __tablename__ = "revision_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=True, index=True)
    scheduled_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, completed, skipped
    interval_days = Column(Integer, default=1, nullable=False)
    ease_factor = Column(Float, default=2.5, nullable=False)  # SuperMemo SM-2 algorithm ease factor
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="revision_schedules")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    reason = Column(Text, nullable=False)
    action_type = Column(String(50), default="quiz", nullable=False)  # quiz, flashcards, summary, tutor
    priority = Column(String(50), default="medium", nullable=False)  # high, medium, low
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="recommendations")
