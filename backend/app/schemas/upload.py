from pydantic import BaseModel
from uuid import UUID


class UploadResponse(BaseModel):
    job_id: str
    project_id: UUID
    source_type: str
    status: str = "queued"
    message: str
