"""
PR Compliance Review API (Agent 7).

POST /pr-review/run — manually review a PR (give PR number, get AI review)
POST /pr-review/webhook — GitHub webhook receiver, auto-triggers on PR open/update

To wire the webhook in GitHub:
  Repo Settings -> Webhooks -> Add webhook
  Payload URL: https://your-deployed-backend/pr-review/webhook
  Content type: application/json
  Secret: same value as GITHUB_WEBHOOK_SECRET in .env
  Events: "Pull requests"
"""
import hashlib
import hmac
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.requirement import Requirement
from app.api.deps import get_current_user
from app.config import settings

router = APIRouter(prefix="/pr-review", tags=["PR Compliance Review"])


class PRReviewRequest(BaseModel):
    project_id: UUID
    pr_number: int
    github_token: Optional[str] = None
    post_comment: bool = False  # if True, posts the review as a PR comment


@router.post("/run", summary="Run Agent 7 (AI PR review) on a Pull Request")
def run_pr_review_endpoint(
    data: PRReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetches the PR's title, description, and changed files from GitHub,
    then runs Agent 7 to check requirement compliance.

    Set post_comment=true to automatically post the AI review as a
    comment on the PR (requires github_token with write access).
    """
    from app.services.github_service import get_pr_details, post_pr_comment
    from app.agent.pr_graph import run_pr_review

    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.github_repo_url:
        raise HTTPException(status_code=400, detail="Project has no github_repo_url set")

    try:
        pr_details = get_pr_details(
            repo_url=project.github_repo_url,
            pr_number=data.pr_number,
            token=data.github_token,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch PR: {str(e)}")

    requirements = db.query(Requirement).filter(
        Requirement.project_id == data.project_id
    ).all()
    project_requirements = [{"id": str(r.id), "text": r.text} for r in requirements]

    try:
        result = run_pr_review(
            pr_title=pr_details["title"],
            pr_body=pr_details["body"],
            pr_changed_files=pr_details["changed_files"],
            project_requirements=project_requirements,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    review = result.get("pr_review")
    if not review:
        raise HTTPException(status_code=500, detail=f"PR review failed: {result.get('errors')}")

    posted = False
    if data.post_comment:
        try:
            posted = post_pr_comment(
                repo_url=project.github_repo_url,
                pr_number=data.pr_number,
                comment_markdown=review["comment_markdown"],
                token=data.github_token,
            )
        except Exception as e:
            review["post_comment_error"] = str(e)

    return {
        "pr_number": data.pr_number,
        "pr_title": pr_details["title"],
        "changed_files_count": len(pr_details["changed_files"]),
        "review": review,
        "comment_posted": posted,
    }


def _verify_signature(payload_body: bytes, signature_header: Optional[str]) -> bool:
    """Verify GitHub webhook HMAC signature using GITHUB_WEBHOOK_SECRET."""
    secret = settings.GITHUB_WEBHOOK_SECRET
    if not secret:
        # No secret configured — accept (dev mode). Warn via return value.
        return True
    if not signature_header:
        return False

    expected = "sha256=" + hmac.new(
        secret.encode(), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@router.post("/webhook", summary="GitHub webhook receiver — auto-runs Agent 7 on PR events")
async def github_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_hub_signature_256: Optional[str] = Header(default=None),
    x_github_event: Optional[str] = Header(default=None),
):
    """
    Receives GitHub webhook events. On `pull_request` events with action
    "opened" or "synchronize" (new commits pushed), automatically runs
    Agent 7 and posts a review comment.

    Matches the project by comparing the webhook's repository full_name
    against projects' github_repo_url.
    """
    body = await request.body()

    if not _verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    if x_github_event != "pull_request":
        return {"status": "ignored", "reason": f"event '{x_github_event}' not handled"}

    payload = json.loads(body)
    action = payload.get("action")
    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "reason": f"action '{action}' not handled"}

    repo_full_name = payload["repository"]["full_name"]  # e.g. "owner/repo"
    pr_number = payload["pull_request"]["number"]

    # Find matching project by repo URL
    candidates = db.query(Project).filter(Project.github_repo_url.isnot(None)).all()
    project = None
    for p in candidates:
        if repo_full_name.lower() in (p.github_repo_url or "").lower():
            project = p
            break

    if not project:
        return {"status": "ignored", "reason": f"no project linked to repo '{repo_full_name}'"}

    from app.services.github_service import get_pr_details, post_pr_comment
    from app.agent.pr_graph import run_pr_review

    try:
        pr_details = get_pr_details(repo_url=project.github_repo_url, pr_number=pr_number)
    except Exception as e:
        return {"status": "error", "reason": f"could not fetch PR: {str(e)}"}

    requirements = db.query(Requirement).filter(Requirement.project_id == project.id).all()
    project_requirements = [{"id": str(r.id), "text": r.text} for r in requirements]

    try:
        result = run_pr_review(
            pr_title=pr_details["title"],
            pr_body=pr_details["body"],
            pr_changed_files=pr_details["changed_files"],
            project_requirements=project_requirements,
        )
    except RuntimeError as e:
        return {"status": "error", "reason": str(e)}

    review = result.get("pr_review")
    if not review:
        return {"status": "error", "reason": f"review failed: {result.get('errors')}"}

    posted = False
    try:
        posted = post_pr_comment(
            repo_url=project.github_repo_url,
            pr_number=pr_number,
            comment_markdown=review["comment_markdown"],
        )
    except Exception as e:
        review["post_comment_error"] = str(e)

    return {
        "status": "reviewed",
        "project": project.name,
        "pr_number": pr_number,
        "compliance_score": review["compliance_score"],
        "recommendation": review["recommendation"],
        "comment_posted": posted,
    }
