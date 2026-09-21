from typing import List, Optional
from pydantic import BaseModel

class RecommendationOut(BaseModel):
    id: str
    topic: str
    title: str
    reason: str
    action: str
    action_type: str
    to: str
    priority: str
    priority_score: float
    recommended_difficulty: str
    recommended_activity: str
    revision_risk: str
    material_id: Optional[str] = None
    icon: Optional[str] = "layers"
    mastery: Optional[float] = 0.0
    recall_reliability: Optional[float] = 0.5
    recent_mistakes: Optional[int] = 0

    class Config:
        from_attributes = True

class DailyRecommendationResponse(BaseModel):
    date: str
    recommendations: List[RecommendationOut]
    ai_study_tip: Optional[str] = None
    total_pending_revisions: int = 0
