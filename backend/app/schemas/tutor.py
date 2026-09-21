from typing import List, Optional
from pydantic import BaseModel, Field

class SourceReferenceOut(BaseModel):
    label: str
    page: str

class TutorAskRequest(BaseModel):
    question: str
    materialId: Optional[str] = Field(default=None, description="CamelCase material id")
    material_id: Optional[str] = Field(default=None, description="Snake_case material id")

    def get_material_id(self) -> Optional[str]:
        return self.materialId or self.material_id

class TutorAskResponse(BaseModel):
    answer: str
    sources: List[SourceReferenceOut] = []
    grounded: bool = True
