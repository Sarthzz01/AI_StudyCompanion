from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class NotificationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    type: str = Field(default="info", max_length=50)  # info, goal, quiz, viva, revision, assessment, feedback

class NotificationOut(BaseModel):
    id: int
    title: str
    body: str  # maps to message column for frontend consistency
    type: str
    read: bool  # maps to is_read column
    time: str
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationsListOut(BaseModel):
    notifications: List[NotificationOut]
    unread_count: int
    total_count: int
