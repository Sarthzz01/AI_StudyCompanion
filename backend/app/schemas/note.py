from typing import Optional, List
from pydantic import BaseModel

class NoteCreate(BaseModel):
    title: str
    topic: Optional[str] = "General"
    material_id: Optional[str] = None
    content: str
    key_points: Optional[List[str]] = []
    examples: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    is_favorite: Optional[bool] = False

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None
    content: Optional[str] = None
    key_points: Optional[List[str]] = None
    examples: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None

class NoteOut(BaseModel):
    id: int
    user_id: int
    material_id: Optional[str] = None
    material_title: Optional[str] = None
    title: str
    topic: Optional[str] = None
    content: str
    key_points: List[str] = []
    examples: List[str] = []
    tags: List[str] = []
    is_favorite: bool = False
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class AIGenerateNotesRequest(BaseModel):
    content_or_prompt: str
    topic: Optional[str] = None

class AIGenerateNotesResponse(BaseModel):
    title: str
    topic: str
    content: str
    key_points: List[str] = []
    examples: List[str] = []
    tags: List[str] = []
