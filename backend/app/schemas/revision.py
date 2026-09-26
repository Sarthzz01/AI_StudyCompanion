from typing import List, Optional
from pydantic import BaseModel

class RevisionItemOut(BaseModel):
    id: int | str
    topic: str
    material_id: Optional[str] = "data-structures"
    scheduled_date: str
    interval_days: int
    ease_factor: float
    repetition_count: int
    mastery: float
    recall_reliability: float
    retention_estimate: Optional[int] = None
    difficulty: Optional[str] = "medium"
    status: str  # overdue, due_today, upcoming
    is_due: Optional[bool] = False
    last_reviewed: Optional[str] = None

    class Config:
        from_attributes = True

class RevisionDueResponse(BaseModel):
    date: str
    total_due: int
    revisions: List[RevisionItemOut]
