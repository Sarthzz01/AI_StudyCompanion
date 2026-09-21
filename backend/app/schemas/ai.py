from typing import Optional
from pydantic import BaseModel

class AIPromptRequest(BaseModel):
    prompt: str
    system_instruction: Optional[str] = "You are an expert AI Study Companion tutor helping students understand concepts clearly."

class AIResponse(BaseModel):
    success: bool
    reply: str
    model: str
    latency_ms: int
    grounded: bool = False
