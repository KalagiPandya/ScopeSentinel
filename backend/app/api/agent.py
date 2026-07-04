"""
Agent pipeline API.

POST /agent/run — runs Agents 1 & 2 on a piece of text:
  1. Extracts requirement statements (Agent 1)
  2. Detects changes vs existing baseline in Qdrant (Agent 2)
  3. Saves NEW requirements to PostgreSQL + Qdrant
  4. Saves detected MODIFICATIONS as RequirementChange rows

Requires OPENAI_API_KEY in .env (Agent 1 uses GPT-4o-mini).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.requirement import Requirement, RequirementType, RequirementSource
from app.models.change import RequirementChange, ChangeType, RiskLevel
from app.models.alert import Alert
from app.api.deps import get_current_user

router = APIRouter(prefix="/agent", tags=["AI Agents"])

RISK_LEVEL_MAP = {
    "low": RiskLevel.low,
    "medium": RiskLevel.medium,
    "high": RiskLevel.high,
    "critical": RiskLevel.critical,
}


def _save_alert(db: Session, project_id, change_row: RequirementChange, notification: Optional[dict]):
    """Save an Alert row based on Agent 8's notification decision."""
    if not notification:
        return
    alert = Alert(
        project_id=project_id,
        change_id=change_row.id,
        risk_score=change_row.risk_score,
        risk_level=change_row.risk_level,
        sent_channels=notification.get("sent_channels", []),
    )
    db.add(alert)
    db.commit()


class RunPipelineRequest(BaseModel):
    project_id: UUID
    text: str
    source: str = "document"   # meeting | email | document | jira | github_issue


SOURCE_MAP = {
    "meeting": RequirementSource.meeting,
    "email": RequirementSource.email,
    "document": RequirementSource.document,
    "jira": RequirementSource.jira,
    "github_issue": RequirementSource.github_issue,
}

CHANGE_TYPE_MAP = {
    "new_addition": ChangeType.new_addition,
    "modification": ChangeType.modification,
}


@router.post("/run", summary="Run Agent 1 (Extractor) + Agent 2 (Detector) on text")
def run_agent_pipeline(
    data: RunPipelineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Full pipeline:

    1. Agent 1 reads `text` and extracts requirement statements using GPT-4o-mini
    2. Agent 2 checks each one against Qdrant for semantic similarity
    3. NEW requirements -> saved to PostgreSQL + embedded in Qdrant
    4. MODIFIED requirements -> saved as RequirementChange rows with word_diff

    Returns a summary of what was found and saved.
    """
    from app.agent.graph import run_pipeline
    from app.services.qdrant_service import store_requirement, create_collection_if_not_exists

    source_enum = SOURCE_MAP.get(data.source, RequirementSource.document)

    # ── Run the LangGraph pipeline ──────────────────────────────────────────
    try:
        result = run_pipeline(
            project_id=str(data.project_id),
            raw_text=data.text,
            source=data.source,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if result.get("status") == "error" and not result.get("extracted_requirements"):
        raise HTTPException(
            status_code=500,
            detail=f"Agent pipeline failed: {result.get('errors')}",
        )

    extracted = result.get("extracted_requirements", [])
    detected_changes = result.get("detected_changes", [])
    notifications = result.get("notifications", [])

    # Build a quick lookup: text -> change info (for new_addition / modification)
    change_by_text = {c["new_text"]: c for c in detected_changes}

    # Build a quick lookup: text -> notification (Agent 8 result)
    notification_by_text = {}
    for idx, change in enumerate(detected_changes):
        if idx < len(notifications):
            notification_by_text[change["new_text"]] = notifications[idx]

    saved_new = []
    saved_modifications = []

    create_collection_if_not_exists()

    for req in extracted:
        text = req["text"]
        change = change_by_text.get(text)

        if change is None:
            # no_change — already exists, skip saving
            continue

        if change["change_type"] == "new_addition":
            # Save brand new requirement to PostgreSQL
            new_req = Requirement(
                project_id=data.project_id,
                text=text,
                type=RequirementType(req.get("type", "functional")),
                source=source_enum,
                confidence_score=req.get("confidence", 0.8),
            )
            db.add(new_req)
            db.commit()
            db.refresh(new_req)

            # Embed it in Qdrant for future comparisons
            point_id = store_requirement(
                requirement_id=str(new_req.id),
                project_id=str(data.project_id),
                text=text,
            )
            new_req.qdrant_point_id = point_id
            db.commit()

            # Log as a change record too (new_addition)
            change_row = RequirementChange(
                project_id=data.project_id,
                old_requirement_id=None,
                new_requirement_id=new_req.id,
                change_type=ChangeType.new_addition,
                similarity_score=change["similarity_score"],
                word_diff=None,
                impact_map=change.get("impact"),
                risk_score=change.get("risk", {}).get("risk_score"),
                risk_level=RISK_LEVEL_MAP.get(change.get("risk", {}).get("risk_level")),
                risk_justification=change.get("risk", {}).get("justification"),
            )
            db.add(change_row)
            db.commit()
            db.refresh(change_row)
            _save_alert(db, data.project_id, change_row, notification_by_text.get(text))

            saved_new.append({
                "id": str(new_req.id),
                "text": text,
                "impact": change.get("impact"),
                "risk": change.get("risk"),
                "notification": notification_by_text.get(text),
            })

        elif change["change_type"] == "modification":
            similar = change["similar_requirement"]
            old_req_id = similar["requirement_id"] if similar else None

            # Save the NEW version as a new Requirement row
            new_req = Requirement(
                project_id=data.project_id,
                text=text,
                type=RequirementType(req.get("type", "functional")),
                source=source_enum,
                confidence_score=req.get("confidence", 0.8),
            )
            db.add(new_req)
            db.commit()
            db.refresh(new_req)

            point_id = store_requirement(
                requirement_id=str(new_req.id),
                project_id=str(data.project_id),
                text=text,
            )
            new_req.qdrant_point_id = point_id
            db.commit()

            # Log the change with word_diff
            change_row = RequirementChange(
                project_id=data.project_id,
                old_requirement_id=old_req_id,
                new_requirement_id=new_req.id,
                change_type=ChangeType.modification,
                similarity_score=change["similarity_score"],
                word_diff=change["word_diff"],
                impact_map=change.get("impact"),
                risk_score=change.get("risk", {}).get("risk_score"),
                risk_level=RISK_LEVEL_MAP.get(change.get("risk", {}).get("risk_level")),
                risk_justification=change.get("risk", {}).get("justification"),
            )
            db.add(change_row)
            db.commit()
            db.refresh(change_row)
            _save_alert(db, data.project_id, change_row, notification_by_text.get(text))

            saved_modifications.append({
                "id": str(new_req.id),
                "text": text,
                "old_requirement_id": old_req_id,
                "similarity_score": change["similarity_score"],
                "word_diff": change["word_diff"],
                "impact": change.get("impact"),
                "risk": change.get("risk"),
                "notification": notification_by_text.get(text),
            })

    return {
        "status": result.get("status"),
        "errors": result.get("errors", []),
        "total_extracted": len(extracted),
        "total_changes_detected": len(detected_changes),
        "new_requirements_saved": saved_new,
        "modifications_saved": saved_modifications,
        "summary": (
            f"Extracted {len(extracted)} requirement(s). "
            f"Found {len(saved_new)} new and {len(saved_modifications)} modified "
            f"requirement(s)."
        ),
    }
