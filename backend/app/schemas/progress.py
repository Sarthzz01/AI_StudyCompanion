from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ProgressStats(BaseModel):
    accuracy: int
    questionsAttempted: int
    studyMinutes: int
    topicsCompleted: int
    totalTopics: int
    overallProgress: int
    flashcardPerformance: Optional[int] = 0
    recallReliability: Optional[int] = 50
    averageMastery: Optional[int] = 0
    vivaSessionsCount: Optional[int] = 0
    averageVivaScore: Optional[float] = 0.0

class PerformanceOverTimeEntry(BaseModel):
    date: str
    accuracy: float

class TopicAccuracyEntry(BaseModel):
    topic: str
    accuracy: float
    mastery: Optional[float] = 0.0
    recall_reliability: Optional[float] = 0.5
    difficulty: Optional[str] = "medium"

class WeeklyStudyEntry(BaseModel):
    day: str
    minutes: int

class RecentlyImprovedEntry(BaseModel):
    topic: str
    change: float

class ProgressOut(BaseModel):
    stats: ProgressStats
    performanceOverTime: List[PerformanceOverTimeEntry]
    topicAccuracy: List[TopicAccuracyEntry]
    weeklyStudy: List[WeeklyStudyEntry]
    recentlyImproved: List[RecentlyImprovedEntry]
    strongTopics: List[str]
    weakTopics: List[str]
    topicsNeedingReview: List[Dict[str, Any]]
    vivaPerformance: Optional[List[Dict[str, Any]]] = []

class TopicProgressOut(BaseModel):
    id: int
    topic: str
    mastery: float
    recall_reliability: float
    quiz_accuracy: float
    flashcard_performance: float
    difficulty: str
    status: str  # strong, weak, improving, needs_review
    last_reviewed: Optional[str] = None
    next_review: Optional[str] = None

class LearnerModelDetailOut(BaseModel):
    id: int
    topic: str
    mastery: float
    recall_reliability: float
    quiz_accuracy: float
    flashcard_performance: float
    difficulty: str
    last_reviewed: Optional[str] = None
    next_review: Optional[str] = None
    recent_performance: List[Dict[str, Any]] = []
    signals: List[Dict[str, Any]] = []
    recommended_action: str
    ai_insight: Optional[str] = None

class StudySessionCreate(BaseModel):
    duration_minutes: int = Field(..., ge=1, le=1440)
    session_type: str = "reading"  # reading, quiz, flashcards, tutor
    material_id: Optional[str] = None
    topic: Optional[str] = None

class StudySessionOut(BaseModel):
    id: int
    duration_minutes: int
    session_type: str
    material_id: Optional[str] = None
    topic: Optional[str] = None
    start_time: str

class GoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    type: str = "weekly"  # daily, weekly
    target: int = Field(..., ge=1)
    unit: str = "topics"  # topics, minutes, quizzes, flashcards

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    current: Optional[int] = None
    target: Optional[int] = None
    completed: Optional[bool] = None

class GoalOut(BaseModel):
    id: int
    title: str
    type: str
    target: int
    current: int
    unit: str
    completed: bool
    created_at: str
