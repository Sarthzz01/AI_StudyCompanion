from typing import List, Optional
from pydantic import BaseModel, Field

class SummarySection(BaseModel):
    id: str
    title: str
    body: str
    points: List[str] = []

class SummaryGenerateRequest(BaseModel):
    materialId: Optional[str] = Field(default=None, description="CamelCase material id")
    material_id: Optional[str] = Field(default=None, description="Snake_case material id")

    def get_material_id(self) -> Optional[str]:
        return self.materialId or self.material_id

class SummaryOut(BaseModel):
    id: str
    materialId: str
    materialTitle: Optional[str] = None
    generatedAt: str
    keyConcepts: List[str] = []
    sections: List[SummarySection] = []
