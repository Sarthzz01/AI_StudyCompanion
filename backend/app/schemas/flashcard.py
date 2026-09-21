from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class FlashcardGenerateRequest(BaseModel):
    material_id: Optional[str] = Field(default=None, alias="materialId")
    topic: Optional[str] = None
    count: Optional[int] = 5
    difficulty: Optional[str] = "medium"

    class Config:
        populate_by_name = True

    def get_material_id(self) -> Optional[str]:
        return self.material_id

class FlashcardOut(BaseModel):
    id: int
    material_id: Optional[str] = None
    topic: Optional[str] = None
    topic_name: Optional[str] = None
    front: str
    back: str
    difficulty: str = "medium"
    source: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FlashcardReviewRequest(BaseModel):
    rating: str = Field(..., description="'easy', 'medium', or 'hard'")

class FlashcardReviewResponse(BaseModel):
    success: bool = True
    card_id: int
    topic: str
    rating: str
    flashcard_performance: float
    message: str
