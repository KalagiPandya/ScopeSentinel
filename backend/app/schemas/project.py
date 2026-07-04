from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    github_repo_url: Optional[str] = None
    sprint_end_date: Optional[datetime] = None
    team_size: int = 5


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    github_repo_url: Optional[str] = None
    sprint_end_date: Optional[datetime] = None
    team_size: Optional[int] = None


class ProjectOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    github_repo_url: Optional[str] = None
    sprint_end_date: Optional[datetime] = None
    team_size: int
    created_at: datetime

    model_config = {"from_attributes": True}
