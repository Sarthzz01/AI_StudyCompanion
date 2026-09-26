from app.database import Base
from app.models.user import Role, User, Profile
from app.models.subject import Subject, Topic
from app.models.material import Material
from app.models.document import DocumentChunk, Summary, TutorInteraction, SourceReference
from app.models.learner import LearnerModel, Progress, RevisionSchedule, Recommendation
from app.models.study import Quiz, Question, Flashcard, QuizAttempt, QuizAnswer, Performance, StudySession, Notification, Analytics, Goal, Note
from app.models.viva import VivaSession, VivaQuestion, VivaAnswer, VivaEvaluation
from app.models.assessment import Assessment, AssessmentAssignment, AssessmentSubmission, InstructorFeedback

__all__ = [
    "Base",
    "Role",
    "User",
    "Profile",
    "Subject",
    "Topic",
    "Material",
    "DocumentChunk",
    "Summary",
    "TutorInteraction",
    "SourceReference",
    "LearnerModel",
    "Progress",
    "RevisionSchedule",
    "Recommendation",
    "Quiz",
    "Question",
    "Flashcard",
    "QuizAttempt",
    "QuizAnswer",
    "Performance",
    "StudySession",
    "Goal",
    "Notification",
    "Analytics",
    "Note",
    "VivaSession",
    "VivaQuestion",
    "VivaAnswer",
    "VivaEvaluation",
    "Assessment",
    "AssessmentAssignment",
    "AssessmentSubmission",
    "InstructorFeedback",
]
