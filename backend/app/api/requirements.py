from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.requirement import Requirement
from app.models.user import User
from app.schemas.requirement import RequirementCreate, RequirementOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/requirements", tags=["Requirements"])


@router.post("/", response_model=RequirementOut)
def create_requirement(data: RequirementCreate, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    req = Requirement(**data.model_dump())
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.get("/project/{project_id}", response_model=List[RequirementOut])
def list_requirements(project_id: UUID, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    return db.query(Requirement).filter(
        Requirement.project_id == project_id
    ).order_by(Requirement.created_at.desc()).all()


@router.get("/{req_id}", response_model=RequirementOut)
def get_requirement(req_id: UUID, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    r = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return r


@router.delete("/{req_id}")
def delete_requirement(req_id: UUID, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    r = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Requirement not found")
    db.delete(r)
    db.commit()
    return {"message": "Deleted"}
