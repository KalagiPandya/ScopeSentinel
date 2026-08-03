"""
GitHub Intelligence API (Agents 3 & 4).

POST /github/scan-coverage — the signature ScopeSentinel feature:
  1. Agent 3 scans the connected GitHub repository
  2. Agent 4 estimates a Coverage Score (0-100%) for EVERY requirement
     in the project, with found/missing implementation details
  3. Results saved to coverage_scores table
  4. Also updates the project's github_repo_url

GET /github/coverage/project/{project_id} — coverage dashboard data
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.requirement import Requirement
from app.models.coverage import CoverageScore
from app.api.deps import get_current_user

router = APIRouter(prefix="/github", tags=["GitHub Intelligence"])


class ScanRequest(BaseModel):
    project_id: UUID
    repo_url: str                    # e.g. "https://github.com/owner/repo"
    github_token: Optional[str] = None  # required for private repos
    requirement_ids: Optional[List[UUID]] = None  # if None, scans ALL requirements


@router.post("/scan-coverage",
              summary="Scan GitHub repo + calculate Requirement Coverage Score for all requirements")
def scan_coverage(
    data: ScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    THE SIGNATURE FEATURE.

    1. Connects to the GitHub repository (Agent 3)
    2. Classifies all files (frontend/backend/database/test/config)
    3. For each requirement, Agent 4 estimates coverage_percent,
       found_implementations, and missing_implementations
    4. Saves/updates CoverageScore rows in PostgreSQL

    Requires OPENAI_API_KEY in .env. For private repos, pass github_token
    (a GitHub Personal Access Token with `repo` read scope).
    """
    from app.agent.github_graph import run_github_pipeline

    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Which requirements to check
    query = db.query(Requirement).filter(Requirement.project_id == data.project_id)
    if data.requirement_ids:
        query = query.filter(Requirement.id.in_(data.requirement_ids))
    requirements = query.all()

    if not requirements:
        raise HTTPException(status_code=400, detail="No requirements found for this project")

    requirements_to_check = [{"id": str(r.id), "text": r.text} for r in requirements]

    # Run Agent 3 + Agent 4
    try:
        result = run_github_pipeline(
            project_id=str(data.project_id),
            repo_url=data.repo_url,
            requirements_to_check=requirements_to_check,
            github_token=data.github_token,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=f"GitHub scan failed: {result.get('errors')}")

    repo_summary = result.get("repo_summary")
    coverage_results = result.get("coverage_results", [])

    # Save repo URL on project if changed
    if project.github_repo_url != data.repo_url:
        project.github_repo_url = data.repo_url
        db.commit()

    # Upsert CoverageScore rows
    saved = []
    for cov in coverage_results:
        req_id = cov["requirement_id"]
        existing = db.query(CoverageScore).filter(
            CoverageScore.requirement_id == req_id
        ).first()

        if existing:
            existing.coverage_percent = cov["coverage_percent"]
            existing.found_implementations = cov["found_implementations"]
            existing.missing_implementations = cov["missing_implementations"]
            from datetime import datetime
            existing.last_scanned_at = datetime.utcnow()
        else:
            existing = CoverageScore(
                requirement_id=req_id,
                coverage_percent=cov["coverage_percent"],
                found_implementations=cov["found_implementations"],
                missing_implementations=cov["missing_implementations"],
            )
            db.add(existing)

        db.commit()
        saved.append({
            "requirement_id": req_id,
            "requirement_text": cov["requirement_text"],
            "coverage_percent": cov["coverage_percent"],
            "found_implementations": cov["found_implementations"],
            "missing_implementations": cov["missing_implementations"],
            "status": (
                "fully_implemented" if cov["coverage_percent"] >= 90 else
                "partially_implemented" if cov["coverage_percent"] >= 50 else
                "not_implemented"
            ),
        })

    avg_coverage = round(sum(c["coverage_percent"] for c in saved) / len(saved), 1) if saved else 0.0

    return {
        "repo_summary": {
            "repo_name": repo_summary.get("repo_name"),
            "description": repo_summary.get("description"),
            "file_counts": repo_summary.get("file_counts"),
            "total_files": repo_summary.get("total_files"),
            "recent_commits": repo_summary.get("recent_commits"),
        } if repo_summary else None,
        "coverage_results": saved,
        "overall_coverage_percent": avg_coverage,
        "total_requirements_scanned": len(saved),
        "errors": result.get("errors", []),
    }


@router.get("/coverage/project/{project_id}",
            summary="Get saved Coverage Scores for a project (dashboard data)")
def get_project_coverage(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns coverage data for the Coverage Center dashboard:
      - per-requirement coverage with GREEN/AMBER/RED status
      - overall project coverage percent
      - counts: fully / partially / not implemented
    """
    scores = (
        db.query(CoverageScore, Requirement)
        .join(Requirement, CoverageScore.requirement_id == Requirement.id)
        .filter(Requirement.project_id == project_id)
        .all()
    )

    if not scores:
        return {
            "overall_coverage_percent": 0.0,
            "fully_implemented": 0,
            "partially_implemented": 0,
            "not_implemented": 0,
            "requirements": [],
            "message": "No coverage data yet. Run POST /github/scan-coverage first.",
        }

    requirements = []
    for cov, req in scores:
        status = (
            "fully_implemented" if cov.coverage_percent >= 90 else
            "partially_implemented" if cov.coverage_percent >= 50 else
            "not_implemented"
        )
        requirements.append({
            "requirement_id": str(req.id),
            "requirement_text": req.text,
            "coverage_percent": cov.coverage_percent,
            "status": status,
            "found_implementations": cov.found_implementations,
            "missing_implementations": cov.missing_implementations,
            "last_scanned_at": cov.last_scanned_at.isoformat(),
        })

    avg = round(sum(r["coverage_percent"] for r in requirements) / len(requirements), 1)

    return {
        "overall_coverage_percent": avg,
        "fully_implemented": len([r for r in requirements if r["status"] == "fully_implemented"]),
        "partially_implemented": len([r for r in requirements if r["status"] == "partially_implemented"]),
        "not_implemented": len([r for r in requirements if r["status"] == "not_implemented"]),
        "requirements": requirements,
    }
