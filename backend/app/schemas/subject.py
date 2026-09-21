from typing import List, Optional
from pydantic import BaseModel

class TopicOut(BaseModel):
    id: int
    subject_id: int
    name: str
    description: Optional[str] = None
    order_index: int = 0
    difficulty_level: str = "medium"

    class Config:
        from_attributes = True

class SubjectOut(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    topics_count: int = 0
    topics: List[TopicOut] = []

    class Config:
        from_attributes = True
