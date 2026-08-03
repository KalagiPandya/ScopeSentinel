import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    github_repo_url = Column(String(500), nullable=True)
    github_token_encrypted = Column(String(500), nullable=True)
    sprint_end_date = Column(DateTime, nullable=True)
    team_size = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
