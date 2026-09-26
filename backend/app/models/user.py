from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)  # 'student', 'instructor', 'admin'
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    role = relationship("Role", back_populates="users")
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    materials = relationship("Material", back_populates="user", cascade="all, delete-orphan")
    learner_models = relationship("LearnerModel", back_populates="user", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="user", cascade="all, delete-orphan")
    performances = relationship("Performance", back_populates="user", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("Progress", back_populates="user", uselist=False, cascade="all, delete-orphan")
    revision_schedules = relationship("RevisionSchedule", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="user", cascade="all, delete-orphan")
    tutor_interactions = relationship("TutorInteraction", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    study_plan_tasks = relationship("StudyPlanTask", back_populates="user", cascade="all, delete-orphan")
    viva_sessions = relationship("VivaSession", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    created_assessments = relationship("Assessment", foreign_keys="[Assessment.instructor_id]", back_populates="instructor", cascade="all, delete-orphan")
    assigned_assessments = relationship("AssessmentAssignment", foreign_keys="[AssessmentAssignment.instructor_id]", back_populates="instructor", cascade="all, delete-orphan")
    assessment_submissions = relationship("AssessmentSubmission", foreign_keys="[AssessmentSubmission.student_id]", back_populates="student", cascade="all, delete-orphan")
    instructor_feedbacks_given = relationship("InstructorFeedback", foreign_keys="[InstructorFeedback.instructor_id]", back_populates="instructor", cascade="all, delete-orphan")
    instructor_feedbacks_received = relationship("InstructorFeedback", foreign_keys="[InstructorFeedback.student_id]", back_populates="student", cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    preferences_json = Column(JSON, default=dict, nullable=False)  # difficulty, sessionLength, alerts, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="profile")
