from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.change import RequirementChange
from app.models.user import User
from app.schemas.change import ChangeOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/changes", tags=["Changes"])


@router.get("/project/{project_id}", response_model=List[ChangeOut])
def list_changes(project_id: UUID, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    return db.query(RequirementChange).filter(
        RequirementChange.project_id == project_id
    ).order_by(RequirementChange.detected_at.desc()).all()


@router.get("/{change_id}", response_model=ChangeOut)
def get_change(change_id: UUID, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    c = db.query(RequirementChange).filter(RequirementChange.id == change_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Change not found")
    return c
