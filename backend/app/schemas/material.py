from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class MaterialTopic(BaseModel):
    name: str
    progress: int = 0

class MaterialActivity(BaseModel):
    id: int
    label: str
    detail: str
    time: str

class MaterialCreate(BaseModel):
    title: str
    type: str = "PDF"
    pages: int = 0
    description: Optional[str] = None
    subject_id: Optional[int] = None
    color: Optional[str] = "brand"

class MaterialOut(BaseModel):
    id: str
    title: str
    type: str
    pages: int
    topicsCount: int
    lastStudied: str
    progress: int
    color: str
    description: str
    processing_status: Optional[str] = "ready"
    topics: List[Dict[str, Any]] = []
    recentActivity: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True
