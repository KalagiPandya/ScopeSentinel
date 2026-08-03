from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.models.change import RequirementChange, RiskLevel
from app.models.requirement import Requirement
from app.models.coverage import CoverageScore
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/project/{project_id}/summary",
            summary="Dashboard summary — requirements, changes, risk, coverage")
def project_summary(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_reqs = db.query(Requirement).filter(
        Requirement.project_id == project_id).count()

    total_changes = db.query(RequirementChange).filter(
        RequirementChange.project_id == project_id).count()

    risk_dist = {}
    for level in RiskLevel:
        risk_dist[level.value] = db.query(RequirementChange).filter(
            RequirementChange.project_id == project_id,
            RequirementChange.risk_level == level,
        ).count()

    scores = (
        db.query(CoverageScore)
        .join(Requirement, CoverageScore.requirement_id == Requirement.id)
        .filter(Requirement.project_id == project_id)
        .all()
    )
    avg_cov = round(sum(s.coverage_percent for s in scores) / len(scores), 1) if scores else 0.0

    return {
        "total_requirements": total_reqs,
        "total_changes":      total_changes,
        "risk_distribution":  risk_dist,
        "coverage": {
            "average_percent":       avg_cov,
            "fully_implemented":     len([s for s in scores if s.coverage_percent >= 90]),
            "partially_implemented": len([s for s in scores if 50 <= s.coverage_percent < 90]),
            "not_implemented":       len([s for s in scores if s.coverage_percent < 50]),
            "total_scanned":         len(scores),
        },
    }
