"""
Seed script — run ONCE after migrations.
Creates 3 users, 1 project, 15 sample requirements.

Run from the root ScopeSentinel/ folder:
    python scripts/seed.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal, engine, Base
from app import models  # noqa
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.requirement import Requirement, RequirementType, RequirementSource
from app.services.auth_service import hash_password
from datetime import datetime, timedelta

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Prevent double-seeding
if db.query(User).filter(User.email == "pm@scopesentinel.com").first():
    print("Already seeded — skipping.")
    db.close()
    sys.exit(0)

print("Seeding database...")

# Users
pm  = User(name="Rahul Sharma", email="pm@scopesentinel.com",
           hashed_password=hash_password("password123"), role=UserRole.pm)
dev = User(name="Priya Patel",  email="dev@scopesentinel.com",
           hashed_password=hash_password("password123"), role=UserRole.developer)
qa  = User(name="Amit Singh",   email="qa@scopesentinel.com",
           hashed_password=hash_password("password123"), role=UserRole.qa)
db.add_all([pm, dev, qa])
db.commit()
print("  Users created")

# Project
project = Project(
    name="College Management System",
    description="Full-stack system for managing students, courses, and attendance",
    github_repo_url="https://github.com/demo/college-management",
    sprint_end_date=datetime.utcnow() + timedelta(days=14),
    team_size=5,
)
db.add(project)
db.commit()
print(f"  Project created  id={project.id}")

# Requirements
texts = [
    "Students must be able to register using their college email address",
    "The system must support OTP verification during student login",
    "Admin can add, edit, and delete student records from the dashboard",
    "Students can view their attendance percentage for each subject",
    "The system must send email notifications when attendance falls below 75 percent",
    "Faculty can upload marks for mid-semester and end-semester examinations",
    "Students can download their marksheet as a PDF from the portal",
    "The system must support role-based access for Admin, Faculty, and Student",
    "All API endpoints must respond within 2 seconds under normal load",
    "The system must maintain an audit log of all admin actions",
    "Students can apply for leave through the portal with reason and duration",
    "Faculty can approve or reject leave applications with comments",
    "The dashboard must display real-time attendance and performance charts",
    "The system must support Hindi and English language interface",
    "Student data must be encrypted at rest using AES-256",
]
for t in texts:
    db.add(Requirement(
        project_id=project.id,
        text=t,
        type=RequirementType.functional,
        source=RequirementSource.document,
        confidence_score=0.95,
    ))
db.commit()
print(f"  {len(texts)} requirements created")

print()
print("=" * 55)
print("Seed complete!")
print(f"  Project ID : {project.id}")
print(f"  PM login   : pm@scopesentinel.com  / password123")
print(f"  Dev login  : dev@scopesentinel.com / password123")
print(f"  QA login   : qa@scopesentinel.com  / password123")
print("=" * 55)
db.close()
