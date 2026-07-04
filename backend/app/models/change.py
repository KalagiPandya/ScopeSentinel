import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, Float, DateTime, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from app.database import Base


class ChangeType(str, enum.Enum):
    new_addition = "new_addition"
    modification = "modification"
    deletion = "deletion"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RequirementChange(Base):
    __tablename__ = "requirement_changes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True),
                        ForeignKey("projects.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    old_requirement_id = Column(UUID(as_uuid=True),
                                ForeignKey("requirements.id", ondelete="SET NULL"),
                                nullable=True)
    new_requirement_id = Column(UUID(as_uuid=True),
                                ForeignKey("requirements.id", ondelete="CASCADE"),
                                nullable=False)
    change_type = Column(Enum(ChangeType), nullable=False)
    similarity_score = Column(Float, nullable=True)
    word_diff = Column(JSON, nullable=True)
    impact_map = Column(JSON, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(Enum(RiskLevel), nullable=True)
    risk_justification = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
