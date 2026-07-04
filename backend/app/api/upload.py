import os
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, UploadFile, File, Form
import aiofiles
from app.models.user import User
from app.schemas.upload import UploadResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/document", response_model=UploadResponse)
async def upload_document(
    project_id: UUID = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF, DOCX, or audio file. Agent processing wired in Day 6."""
    job_id = str(uuid4())
    safe_name = file.filename.replace(" ", "_")
    path = f"{UPLOAD_DIR}/{job_id}_{safe_name}"
    async with aiofiles.open(path, "wb") as f:
        await f.write(await file.read())
    return UploadResponse(
        job_id=job_id, project_id=project_id,
        source_type=file.content_type or "unknown",
        status="queued",
        message=f"File saved. Agent pipeline coming Day 6. job_id={job_id}",
    )


@router.post("/text", response_model=UploadResponse)
async def upload_text(
    project_id: UUID = Form(...),
    text: str = Form(...),
    source: str = Form(default="email"),
    current_user: User = Depends(get_current_user),
):
    """Submit raw text (email / meeting notes). Agent processing wired in Day 6."""
    job_id = str(uuid4())
    return UploadResponse(
        job_id=job_id, project_id=project_id,
        source_type=source, status="queued",
        message=f"Text received. Agent pipeline coming Day 6. job_id={job_id}",
    )
