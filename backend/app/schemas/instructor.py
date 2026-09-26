from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# ==========================================
# Assessment Schemas
# ==========================================

class AssessmentQuestionItem(BaseModel):
    id: int = Field(..., description="Unique question order/identifier within assessment")
    question_text: str = Field(..., min_length=5)
    question_type: str = Field(default="multiple_choice")  # multiple_choice, open_concept
    options: List[str] = Field(default_factory=list)
    correct_answer: int = Field(..., description="Zero-based index of the correct option")
    points: int = Field(default=10, ge=1)
    explanation: Optional[str] = None
    concept_tested: Optional[str] = None
    difficulty: Optional[str] = "medium"

class AssessmentCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    topic: str = Field(..., min_length=2, max_length=200)
    subject_id: Optional[int] = None
    description: Optional[str] = None
    difficulty: str = Field(default="medium")  # easy, medium, hard, mixed
    time_limit_minutes: int = Field(default=30, ge=5, le=180)
    total_points: int = Field(default=100, ge=10)
    pass_percentage: float = Field(default=60.0, ge=0.0, le=100.0)
    questions: List[AssessmentQuestionItem] = Field(..., min_items=1)
    is_published: bool = True

class AssessmentUpdateRequest(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None
    subject_id: Optional[int] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    total_points: Optional[int] = None
    pass_percentage: Optional[float] = None
    questions: Optional[List[AssessmentQuestionItem]] = None
    is_published: Optional[bool] = None

class AssessmentResponse(BaseModel):
    id: int
    instructor_id: int
    instructor_name: Optional[str] = None
    subject_id: Optional[int] = None
    subject_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    topic: str
    difficulty: str
    time_limit_minutes: int
    total_points: int
    pass_percentage: float
    question_count: int
    questions: List[AssessmentQuestionItem]
    is_published: bool
    created_at: datetime
    updated_at: datetime
    total_assignments: Optional[int] = 0
    total_submissions: Optional[int] = 0
    average_score: Optional[float] = 0.0

    class Config:
        from_attributes = True

# ==========================================
# Assignment Schemas
# ==========================================

class AssignAssessmentRequest(BaseModel):
    assigned_to_all: bool = True
    student_id: Optional[int] = None
    due_date: Optional[datetime] = None
    instructions: Optional[str] = None

class AssignmentResponse(BaseModel):
    id: int
    assessment_id: int
    assessment_title: str
    topic: str
    instructor_id: int
    assigned_to_all: bool
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    due_date: Optional[datetime] = None
    instructions: Optional[str] = None
    status: str
    created_at: datetime
    submissions_count: Optional[int] = 0

# ==========================================
# Student Submission & Progress Schemas
# ==========================================

class StudentSubmissionAnswer(BaseModel):
    question_id: int
    selected_option: int

class SubmitAssessmentRequest(BaseModel):
    assignment_id: Optional[int] = None
    answers: List[StudentSubmissionAnswer]
    time_spent_seconds: int = 0

class AssessmentSubmissionResponse(BaseModel):
    id: int
    assessment_id: int
    assessment_title: str
    student_id: int
    student_name: str
    student_email: str
    score: float
    total_points: int
    percentage: float
    passed: bool
    time_spent_seconds: int
    status: str
    submitted_at: datetime
    answers_count: int

# ==========================================
# Student List & Individual Profile Schemas
# ==========================================

class StudentSummaryItem(BaseModel):
    id: int
    name: str
    email: str
    avatar_url: Optional[str] = None
    joined_date: str
    overall_mastery: float
    topics_tracked: int
    quizzes_completed: int
    average_quiz_score: float
    viva_sessions_completed: int
    average_viva_score: float
    risk_status: str  # 'excelling', 'on_track', 'at_risk'
    last_active: Optional[datetime] = None
    feedbacks_count: int

class StudentTopicMasteryItem(BaseModel):
    topic: str
    mastery: float
    quiz_accuracy: float
    flashcard_score: float
    viva_score: float
    recall_probability: float
    last_reviewed: Optional[datetime] = None
    status: str  # 'mastered', 'proficient', 'needs_practice'

class StudentDetailResponse(BaseModel):
    id: int
    name: str
    email: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    joined_date: str
    overall_mastery: float
    total_study_minutes: int
    streak_days: int
    risk_status: str
    topics: List[StudentTopicMasteryItem]
    recent_quizzes: List[Dict[str, Any]]
    recent_vivas: List[Dict[str, Any]]
    submissions: List[Dict[str, Any]]
    feedbacks: List[Dict[str, Any]]

# ==========================================
# Feedback Schemas
# ==========================================

class CreateFeedbackRequest(BaseModel):
    student_id: int
    assessment_id: Optional[int] = None
    submission_id: Optional[int] = None
    topic: Optional[str] = None
    feedback_type: str = Field(default="general_guidance")  # assessment_review, topic_intervention, general_guidance, commendation
    feedback_text: str = Field(..., min_length=5)
    action_items: List[str] = Field(default_factory=list)

class FeedbackResponse(BaseModel):
    id: int
    instructor_id: int
    instructor_name: str
    student_id: int
    student_name: str
    student_email: str
    assessment_id: Optional[int] = None
    assessment_title: Optional[str] = None
    topic: Optional[str] = None
    feedback_type: str
    feedback_text: str
    action_items: List[str]
    is_read: bool
    created_at: datetime

# ==========================================
# Analytics & Reports Schemas
# ==========================================

class TopicAnalyticsItem(BaseModel):
    topic: str
    subject_name: Optional[str] = None
    average_mastery: float
    students_count: int
    mastered_count: int
    at_risk_count: int
    average_quiz_accuracy: float
    average_viva_score: float
    common_weakness_summary: str

class ClassAnalyticsOverview(BaseModel):
    total_students: int
    active_students_7d: int
    average_class_mastery: float
    at_risk_students_count: int
    excelling_students_count: int
    total_assessments_created: int
    total_submissions_received: int
    average_assessment_score: float
    class_quizzes_completed: int
    class_vivas_completed: int
    total_study_hours: float
    topic_distribution: List[TopicAnalyticsItem]
    score_distribution: Dict[str, int]  # {'90-100': 5, '80-89': 12, ...}

class ClassSummaryReport(BaseModel):
    generated_at: datetime
    instructor_name: str
    total_enrolled: int
    class_average_mastery: float
    assessment_summary: Dict[str, Any]
    topic_breakdown: List[TopicAnalyticsItem]
    top_performers: List[Dict[str, Any]]
    students_needing_intervention: List[Dict[str, Any]]
    recommended_class_actions: List[str]

# ==========================================
# AI Question Generation Schemas
# ==========================================

class AIGenerateQuestionsRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    subject: Optional[str] = None
    material_id: Optional[str] = None
    difficulty: str = Field(default="medium")  # easy, medium, hard, mixed
    question_count: int = Field(default=5, ge=1, le=15)
    include_explanations: bool = True

class AIGenerateQuestionsResponse(BaseModel):
    topic: str
    difficulty: str
    suggested_title: str
    suggested_time_minutes: int
    suggested_pass_percentage: float
    questions: List[AssessmentQuestionItem]
    teaching_notes: Optional[str] = None
