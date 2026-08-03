"""
Jira sync API.

Unlike the old claim in the pitch doc ("watches Jira"), this previously
did not exist in the codebase — /agent/run only accepted manually pasted
text. This endpoint makes that claim true: it pulls real issues from a
Jira Cloud project and runs each one through the same Agent 1+2 pipeline
used everywhere else.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services import jira_service
from app.api.agent import process_text_and_persist

router = APIRouter(prefix="/jira", tags=["Jira Integration"])


@router.get("/test-connection", summary="Verify Jira credentials work")
def jira_test_connection(current_user: User = Depends(get_current_user)):
    try:
        return jira_service.test_connection()
    except jira_service.JiraNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Jira connection failed: {e}")


class JiraSyncRequest(BaseModel):
    project_id: UUID              # ScopeSentinel project to attach requirements to
    jira_project_key: Optional[str] = None   # defaults to JIRA_PROJECT_KEY in .env
    jql: Optional[str] = None                # or pass custom JQL for full control
    max_results: int = 25


@router.post("/sync", summary="Pull Jira issues and run them through the agent pipeline")
def sync_jira(
    data: JiraSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    1. Fetches up to `max_results` issues from Jira (summary + description + comments)
    2. Runs EACH issue's text through Agent 1 (Extractor) + Agent 2 (Change Detector)
    3. Persists new/changed requirements exactly like a manual /agent/run call

    Requires JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN in .env.
    """
    try:
        issues = jira_service.fetch_issues(
            project_key=data.jira_project_key,
            jql=data.jql,
            max_results=data.max_results,
        )
    except jira_service.JiraNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch Jira issues: {e}")

    results = []
    for issue in issues:
        if not issue["text"].strip():
            continue
        try:
            outcome = process_text_and_persist(
                db=db,
                project_id=data.project_id,
                raw_text=issue["text"],
                source="jira",
            )
            results.append({"jira_key": issue["key"], **outcome})
        except HTTPException as e:
            results.append({"jira_key": issue["key"], "status": "error", "detail": e.detail})

    total_new = sum(len(r.get("new_requirements_saved", [])) for r in results)
    total_mod = sum(len(r.get("modifications_saved", [])) for r in results)

    return {
        "issues_processed": len(results),
        "total_new_requirements": total_new,
        "total_modifications": total_mod,
        "results": results,
    }
