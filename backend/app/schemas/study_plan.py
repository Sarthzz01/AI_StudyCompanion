from typing import List, Optional
from pydantic import BaseModel

class StudyPlanTaskOut(BaseModel):
    id: int
    task_title: str
    topic: str
    material_id: Optional[str] = "data-structures"
    activity: str
    duration_minutes: int
    priority: str
    difficulty: str
    completed: bool = False
    completed_at: Optional[str] = None
    reason: Optional[str] = ""
    action_url: Optional[str] = None

    class Config:
        from_attributes = True

class StudyPlanResponse(BaseModel):
    plan_date: str
    target_minutes: int
    allocated_minutes: int
    completed_count: int
    total_tasks: int
    ai_guidance: Optional[str] = None
    tasks: List[StudyPlanTaskOut]
