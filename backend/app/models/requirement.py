import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class RequirementType(str, enum.Enum):
    functional = "functional"
    non_functional = "non_functional"
    constraint = "constraint"


class RequirementSource(str, enum.Enum):
    meeting = "meeting"
    email = "email"
    document = "document"
    jira = "jira"
    github_issue = "github_issue"


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True),
                        ForeignKey("projects.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    text = Column(Text, nullable=False)
    type = Column(Enum(RequirementType), default=RequirementType.functional)
    source = Column(Enum(RequirementSource), nullable=True)
    confidence_score = Column(Float, default=1.0)
    qdrant_point_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
