from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class QuizGenerateRequest(BaseModel):
    material_id: Optional[str] = Field(default=None, alias="materialId")
    topic: Optional[str] = "All topics"
    difficulty: Optional[str] = "mixed"
    count: Optional[int] = 5

    class Config:
        populate_by_name = True

    def get_material_id(self) -> Optional[str]:
        return self.material_id

class QuestionOut(BaseModel):
    id: int
    question: str
    question_type: str = "multiple_choice"
    options: List[str]
    topic: str
    difficulty: str

    class Config:
        from_attributes = True

class QuizOut(BaseModel):
    id: int
    material_id: Optional[str] = None
    material_title: Optional[str] = None
    topic: str
    difficulty: str
    question_count: int
    created_at: str
    questions: List[QuestionOut] = []

    class Config:
        from_attributes = True

class QuizAttemptStartOut(BaseModel):
    id: int
    quiz_id: int
    material_id: Optional[str] = None
    material_title: Optional[str] = None
    topic: str
    difficulty: str
    status: str
    questions: List[QuestionOut] = []

    class Config:
        from_attributes = True

class QuizSubmitAnswerItem(BaseModel):
    question_id: int
    selected_option: Optional[int] = None

class QuizSubmitRequest(BaseModel):
    answers: List[QuizSubmitAnswerItem] = []

class QuizAnswerReviewOut(BaseModel):
    id: int
    question: str
    topic: str
    options: List[str]
    selected: Optional[int] = None
    answer: int
    correct: bool
    explanation: str

class QuizAttemptResultOut(BaseModel):
    id: str
    quiz_id: int
    material_id: Optional[str] = None
    material_title: Optional[str] = None
    topic: str
    difficulty: str
    score: int
    total: int
    accuracy: float
    date: str
    topicResults: Dict[str, Any] = {}
    strongTopics: List[str] = []
    weakTopics: List[str] = []
    difficultyResults: Dict[str, Any] = {}
    review: List[QuizAnswerReviewOut] = []

class QuizAttemptSummaryOut(BaseModel):
    id: str
    quiz_id: Optional[int] = None
    material_id: Optional[str] = None
    material_title: str
    topic: str
    difficulty: str
    score: int
    total: int
    accuracy: float
    date: str
    status: str
