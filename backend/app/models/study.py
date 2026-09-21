from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(String(100), ForeignKey("materials.id", ondelete="CASCADE"), nullable=True, index=True)
    topic = Column(String(200), nullable=False)
    difficulty = Column(String(50), default="mixed", nullable=False)
    question_count = Column(Integer, default=5, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="quizzes")
    material = relationship("Material", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=True, index=True)
    material_id = Column(String(100), ForeignKey("materials.id", ondelete="SET NULL"), nullable=True, index=True)
    topic_name = Column(String(200), nullable=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="multiple_choice", nullable=False)
    options_json = Column(JSON, default=list, nullable=False)  # ['option1', 'option2', ...]
    correct_answer = Column(String(255), nullable=False)  # option index or text
    explanation = Column(Text, nullable=True)
    difficulty = Column(String(50), default="medium", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    topic = relationship("Topic", back_populates="questions")
    quiz = relationship("Quiz", back_populates="questions")
    material = relationship("Material")

class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=True, index=True)
    material_id = Column(String(100), ForeignKey("materials.id", ondelete="CASCADE"), nullable=True, index=True)
    topic_name = Column(String(200), nullable=True)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    difficulty = Column(String(50), default="medium", nullable=False)
    source = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="flashcards")
    topic = relationship("Topic", back_populates="flashcards")
    material = relationship("Material", back_populates="flashcards")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="SET NULL"), nullable=True, index=True)
    material_id = Column(String(100), ForeignKey("materials.id", ondelete="SET NULL"), nullable=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    topic = Column(String(200), nullable=True)
    difficulty = Column(String(50), default="mixed", nullable=True)
    score = Column(Integer, default=0, nullable=False)
    total_questions = Column(Integer, default=0, nullable=False)
    accuracy = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="in_progress", nullable=False)  # in_progress, completed
    answers_json = Column(JSON, default=list, nullable=False)
    topic_results_json = Column(JSON, default=dict, nullable=False)
    difficulty_results_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")
    material = relationship("Material", back_populates="quiz_attempts")
    answers = relationship("QuizAnswer", back_populates="attempt", cascade="all, delete-orphan")
    performance = relationship("Performance", back_populates="attempt", uselist=False, cascade="all, delete-orphan")

class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True, index=True)
    question_text = Column(Text, nullable=False)
    options_json = Column(JSON, default=list, nullable=False)
    selected_option = Column(Integer, nullable=True)
    correct_answer = Column(Integer, nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)
    explanation = Column(Text, nullable=True)
    topic = Column(String(200), nullable=True)
    difficulty = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question")

class Performance(Base):
    __tablename__ = "performance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quiz_attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    accuracy = Column(Float, nullable=False)
    correct_count = Column(Integer, nullable=False)
    incorrect_count = Column(Integer, nullable=False)
    topic_performance_json = Column(JSON, default=dict, nullable=False)
    difficulty_performance_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="performances")
    attempt = relationship("QuizAttempt", back_populates="performance")

class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(String(100), ForeignKey("materials.id", ondelete="SET NULL"), nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0, nullable=False)
    session_type = Column(String(50), default="reading", nullable=False)  # reading, quiz, flashcards, tutor
    topic = Column(String(200), nullable=True)

    user = relationship("User", back_populates="study_sessions")
    material = relationship("Material", back_populates="study_sessions")

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    type = Column(String(50), default="weekly", nullable=False)  # daily, weekly
    target = Column(Integer, default=5, nullable=False)
    current = Column(Integer, default=0, nullable=False)
    unit = Column(String(50), default="topics", nullable=False)  # topics, minutes, quizzes, flashcards
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="goals")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info", nullable=False)  # info, goal, quiz, alert
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")

class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_data_json = Column(JSON, default=dict, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="analytics")
