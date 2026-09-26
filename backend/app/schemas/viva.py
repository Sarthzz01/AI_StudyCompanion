from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class VivaStartRequest(BaseModel):
    material_id: Optional[str] = None
    topic: str = Field(..., description="Subject topic name, e.g. 'Routing Algorithms' or 'Deadlocks'")
    mode: str = Field(default="basic", description="Viva mode: 'basic', 'technical', or 'interview'")
    difficulty: str = Field(default="medium", description="Difficulty level: 'easy', 'medium', 'hard'")
    total_questions: int = Field(default=4, ge=2, le=10, description="Target number of questions (2 to 10)")


class VivaQuestionOut(BaseModel):
    id: int
    question_index: int
    question_text: str
    difficulty: str
    question_type: str = "main"  # 'main' or 'follow_up'
    ideal_concept_points: List[str] = []

    class Config:
        from_attributes = True


class VivaStartResponse(BaseModel):
    session_id: int
    topic: str
    material_id: Optional[str] = None
    mode: str
    difficulty: str
    status: str
    current_question_index: int
    total_questions: int
    current_question: VivaQuestionOut


class VivaAnswerRequest(BaseModel):
    question_id: int
    answer_text: str = Field(..., min_length=2, description="Student's verbal or written answer")


class VivaEvaluationOut(BaseModel):
    id: Optional[int] = None
    score: float = Field(..., description="0.0 to 100.0 score")
    correctness: float = Field(..., description="0.0 to 100.0 score")
    relevance: float = Field(..., description="0.0 to 100.0 score")
    completeness: float = Field(..., description="0.0 to 100.0 score")
    conceptual_understanding: float = Field(..., description="0.0 to 100.0 score")
    feedback: str
    key_strengths: List[str] = []
    missing_points: List[str] = []
    suggested_follow_up_topic: Optional[str] = None

    class Config:
        from_attributes = True


class VivaAnswerResponse(BaseModel):
    session_id: int
    question_id: int
    evaluation: VivaEvaluationOut
    has_next_question: bool
    next_question: Optional[VivaQuestionOut] = None
    is_session_complete: bool = False


class VivaQAItem(BaseModel):
    question_id: int
    question_index: int
    question_text: str
    question_type: str
    difficulty: str
    ideal_concept_points: List[str] = []
    answer_text: Optional[str] = None
    evaluation: Optional[VivaEvaluationOut] = None


class VivaSessionDetailResponse(BaseModel):
    id: int
    topic: str
    material_id: Optional[str] = None
    mode: str
    difficulty: str
    status: str
    total_questions: int
    completed_questions: int
    overall_score: float
    correctness_score: float
    relevance_score: float
    completeness_score: float
    conceptual_score: float
    strengths: List[str] = []
    weak_areas: List[str] = []
    suggested_improvements: List[str] = []
    overall_feedback: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    transcript: List[VivaQAItem] = []

    class Config:
        from_attributes = True


class VivaSessionOut(BaseModel):
    id: int
    topic: str
    material_id: Optional[str] = None
    mode: str
    difficulty: str
    status: str
    total_questions: int
    overall_score: float
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VivaHistoryResponse(BaseModel):
    total_sessions: int
    average_score: float
    sessions: List[VivaSessionOut]
