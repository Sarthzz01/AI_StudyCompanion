from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    topic = Column(String(200), nullable=False, index=True)
    difficulty = Column(String(50), default="medium", nullable=False)  # easy, medium, hard, mixed
    time_limit_minutes = Column(Integer, default=30, nullable=False)
    total_points = Column(Integer, default=100, nullable=False)
    pass_percentage = Column(Float, default=60.0, nullable=False)
    questions_json = Column(JSON, default=list, nullable=False)  # List of question dicts
    is_published = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    instructor = relationship("User", foreign_keys=[instructor_id], back_populates="created_assessments")
    subject = relationship("Subject")
    assignments = relationship("AssessmentAssignment", back_populates="assessment", cascade="all, delete-orphan")
    submissions = relationship("AssessmentSubmission", back_populates="assessment", cascade="all, delete-orphan")
    feedbacks = relationship("InstructorFeedback", back_populates="assessment", cascade="all, delete-orphan")

class AssessmentAssignment(Base):
    __tablename__ = "assessment_assignments"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to_all = Column(Boolean, default=True, nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # Null if assigned to all
    due_date = Column(DateTime, nullable=True)
    instructions = Column(Text, nullable=True)
    status = Column(String(50), default="active", nullable=False)  # active, closed, archived
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assessment = relationship("Assessment", back_populates="assignments")
    instructor = relationship("User", foreign_keys=[instructor_id], back_populates="assigned_assessments")
    student = relationship("User", foreign_keys=[student_id])
    submissions = relationship("AssessmentSubmission", back_populates="assignment")

class AssessmentSubmission(Base):
    __tablename__ = "assessment_submissions"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id = Column(Integer, ForeignKey("assessment_assignments.id", ondelete="SET NULL"), nullable=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Float, default=0.0, nullable=False)
    total_points = Column(Integer, default=100, nullable=False)
    percentage = Column(Float, default=0.0, nullable=False)
    passed = Column(Boolean, default=False, nullable=False)
    answers_json = Column(JSON, default=list, nullable=False)
    time_spent_seconds = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="submitted", nullable=False)  # submitted, graded
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assessment = relationship("Assessment", back_populates="submissions")
    assignment = relationship("AssessmentAssignment", back_populates="submissions")
    student = relationship("User", foreign_keys=[student_id], back_populates="assessment_submissions")
    feedbacks = relationship("InstructorFeedback", back_populates="submission")

class InstructorFeedback(Base):
    __tablename__ = "instructor_feedback"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="SET NULL"), nullable=True, index=True)
    submission_id = Column(Integer, ForeignKey("assessment_submissions.id", ondelete="SET NULL"), nullable=True, index=True)
    topic = Column(String(200), nullable=True)
    feedback_type = Column(String(50), default="general_guidance", nullable=False)  # assessment_review, topic_intervention, general_guidance, commendation
    feedback_text = Column(Text, nullable=False)
    action_items_json = Column(JSON, default=list, nullable=False)  # List of strings / recommended tasks
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    instructor = relationship("User", foreign_keys=[instructor_id], back_populates="instructor_feedbacks_given")
    student = relationship("User", foreign_keys=[student_id], back_populates="instructor_feedbacks_received")
    assessment = relationship("Assessment", back_populates="feedbacks")
    submission = relationship("AssessmentSubmission", back_populates="feedbacks")
