from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from app.models.change import ChangeType, RiskLevel


class ChangeOut(BaseModel):
    id: UUID
    project_id: UUID
    old_requirement_id: Optional[UUID] = None
    new_requirement_id: UUID
    change_type: ChangeType
    similarity_score: Optional[float] = None
    word_diff: Optional[Any] = None
    impact_map: Optional[Any] = None
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    risk_justification: Optional[str] = None
    detected_at: datetime

    model_config = {"from_attributes": True}
