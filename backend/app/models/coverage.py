import uuid
from datetime import datetime
from sqlalchemy import Column, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from app.database import Base


class CoverageScore(Base):
    __tablename__ = "coverage_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID(as_uuid=True),
                            ForeignKey("requirements.id", ondelete="CASCADE"),
                            nullable=False, index=True)
    coverage_percent = Column(Float, default=0.0, nullable=False)
    found_implementations = Column(JSON, default=list, nullable=False)
    missing_implementations = Column(JSON, default=list, nullable=False)
    last_scanned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
