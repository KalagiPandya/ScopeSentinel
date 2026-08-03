"""
Email sync API.

Same idea as jira.py: makes the pitch doc's "watches emails" claim
actually true by reading a real IMAP inbox instead of requiring a
manual paste into Upload Center.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services import email_service
from app.api.agent import process_text_and_persist

router = APIRouter(prefix="/email", tags=["Email Integration"])


@router.get("/test-connection", summary="Verify IMAP credentials work")
def email_test_connection(current_user: User = Depends(get_current_user)):
    try:
        return email_service.test_connection()
    except email_service.EmailNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"IMAP connection failed: {e}")


class EmailSyncRequest(BaseModel):
    project_id: UUID
    max_results: int = 25
    mark_as_read: bool = False


@router.post("/sync", summary="Pull unread inbox emails and run them through the agent pipeline")
def sync_email(
    data: EmailSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    1. Fetches up to `max_results` unread emails from the configured IMAP inbox
    2. Runs EACH email's subject+body through Agent 1 (Extractor) + Agent 2 (Change Detector)
    3. Persists new/changed requirements exactly like a manual /agent/run call

    Requires IMAP_HOST, IMAP_USER, IMAP_PASSWORD in .env.
    """
    try:
        emails = email_service.fetch_unread_emails(
            max_results=data.max_results,
            mark_as_read=data.mark_as_read,
        )
    except email_service.EmailNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch emails: {e}")

    results = []
    for msg in emails:
        if not msg["text"].strip():
            continue
        try:
            outcome = process_text_and_persist(
                db=db,
                project_id=data.project_id,
                raw_text=msg["text"],
                source="email",
            )
            results.append({"subject": msg["subject"], "from": msg["from"], **outcome})
        except HTTPException as e:
            results.append({"subject": msg["subject"], "status": "error", "detail": e.detail})

    total_new = sum(len(r.get("new_requirements_saved", [])) for r in results)
    total_mod = sum(len(r.get("modifications_saved", [])) for r in results)

    return {
        "emails_processed": len(results),
        "total_new_requirements": total_new,
        "total_modifications": total_mod,
        "results": results,
    }
