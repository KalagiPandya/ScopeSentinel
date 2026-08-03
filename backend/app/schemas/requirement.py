from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.requirement import RequirementType, RequirementSource


class RequirementCreate(BaseModel):
    project_id: UUID
    text: str
    type: RequirementType = RequirementType.functional
    source: Optional[RequirementSource] = None
    confidence_score: float = 1.0


class RequirementOut(BaseModel):
    id: UUID
    project_id: UUID
    text: str
    type: RequirementType
    source: Optional[RequirementSource] = None
    confidence_score: float
    created_at: datetime

    model_config = {"from_attributes": True}
