from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class VivaSession(Base):
    __tablename__ = "viva_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(String(100), ForeignKey("materials.id", ondelete="SET NULL"), nullable=True, index=True)
    topic = Column(String(200), nullable=False, index=True)
    mode = Column(String(50), default="basic", nullable=False)  # 'basic', 'technical', 'interview'
    difficulty = Column(String(50), default="medium", nullable=False)  # 'easy', 'medium', 'hard'
    status = Column(String(50), default="in_progress", nullable=False)  # 'in_progress', 'completed'
    current_question_index = Column(Integer, default=1, nullable=False)
    total_questions = Column(Integer, default=4, nullable=False)
    
    # Aggregated Metrics
    overall_score = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0%
    correctness_score = Column(Float, default=0.0, nullable=False)
    relevance_score = Column(Float, default=0.0, nullable=False)
    completeness_score = Column(Float, default=0.0, nullable=False)
    conceptual_score = Column(Float, default=0.0, nullable=False)
    
    # Reports
    strengths_json = Column(JSON, default=list, nullable=False)
    weak_areas_json = Column(JSON, default=list, nullable=False)
    suggested_improvements_json = Column(JSON, default=list, nullable=False)
    overall_feedback = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="viva_sessions")
    material = relationship("Material")
    questions = relationship("VivaQuestion", back_populates="session", cascade="all, delete-orphan", order_by="VivaQuestion.question_index.asc()")
    answers = relationship("VivaAnswer", back_populates="session", cascade="all, delete-orphan")
    evaluations = relationship("VivaEvaluation", back_populates="session", cascade="all, delete-orphan")


class VivaQuestion(Base):
    __tablename__ = "viva_questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("viva_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_index = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    topic = Column(String(200), nullable=True)
    difficulty = Column(String(50), default="medium", nullable=False)
    question_type = Column(String(50), default="main", nullable=False)  # 'main', 'follow_up'
    parent_question_id = Column(Integer, ForeignKey("viva_questions.id", ondelete="SET NULL"), nullable=True)
    ideal_concept_points_json = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("VivaSession", back_populates="questions")
    answer = relationship("VivaAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan")
    evaluation = relationship("VivaEvaluation", back_populates="question", uselist=False, cascade="all, delete-orphan")


class VivaAnswer(Base):
    __tablename__ = "viva_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("viva_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("viva_questions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("VivaSession", back_populates="answers")
    question = relationship("VivaQuestion", back_populates="answer")
    evaluation = relationship("VivaEvaluation", back_populates="answer", uselist=False, cascade="all, delete-orphan")


class VivaEvaluation(Base):
    __tablename__ = "viva_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("viva_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("viva_questions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    answer_id = Column(Integer, ForeignKey("viva_answers.id", ondelete="CASCADE"), nullable=True, index=True)
    
    score = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0%
    correctness = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0%
    relevance = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0%
    completeness = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0%
    conceptual_understanding = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0%
    
    feedback = Column(Text, nullable=False)
    key_strengths_json = Column(JSON, default=list, nullable=False)
    missing_points_json = Column(JSON, default=list, nullable=False)
    suggested_follow_up_topic = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("VivaSession", back_populates="evaluations")
    question = relationship("VivaQuestion", back_populates="evaluation")
    answer = relationship("VivaAnswer", back_populates="evaluation")
