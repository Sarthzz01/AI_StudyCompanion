from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class SourceReferenceOut(BaseModel):
    label: str
    page: str

class TutorAskRequest(BaseModel):
    message: Optional[str] = Field(default=None, description="The user's question or prompt")
    question: Optional[str] = Field(default=None, description="Alternative field for backward compatibility")
    history: Optional[List[Dict[str, str]]] = Field(default=None, description="Previous messages in conversation [{role, content}]")
    materialId: Optional[str] = Field(default=None, description="CamelCase material id")
    material_id: Optional[str] = Field(default=None, description="Snake_case material id")
    conversationId: Optional[str] = Field(default=None, description="CamelCase conversation id")
    conversation_id: Optional[str] = Field(default=None, description="Snake_case conversation id")

    def get_query(self) -> str:
        q = self.message if self.message is not None else (self.question or "")
        return q.strip()

    def get_material_id(self) -> Optional[str]:
        return self.materialId or self.material_id

    def get_conversation_id(self) -> Optional[str]:
        return self.conversationId or self.conversation_id

class TutorAskResponse(BaseModel):
    answer: str
    sources: List[SourceReferenceOut] = []
    grounded: bool = False
    model: Optional[str] = None
    conversation_id: Optional[str] = None
    title: Optional[str] = None

class TutorConversationSummary(BaseModel):
    conversation_id: str
    title: str
    last_message: Optional[str] = None
    updated_at: str
    created_at: str
    message_count: int
    material_id: Optional[str] = None

class TutorHistoryItemOut(BaseModel):
    id: int
    question: str
    answer: str
    grounded: bool = False
    material_id: Optional[str] = None
    conversation_id: Optional[str] = None
    created_at: str
    sources: List[SourceReferenceOut] = []

class TutorConversationRenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="The custom renamed title")
