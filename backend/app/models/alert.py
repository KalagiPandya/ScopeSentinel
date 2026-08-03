import uuid
from datetime import datetime
from sqlalchemy import Column, Float, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSON
from app.database import Base
from app.models.change import RiskLevel


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True),
                        ForeignKey("projects.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    change_id = Column(UUID(as_uuid=True),
                       ForeignKey("requirement_changes.id", ondelete="SET NULL"),
                       nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(Enum(RiskLevel), nullable=True)
    sent_channels = Column(JSON, default=list, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
