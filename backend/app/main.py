from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

# Import models so SQLAlchemy registers all tables
from app.database import engine, Base, SessionLocal
from app import models  # noqa: F401 — side-effect import
from app.config import settings
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.requirement import Requirement, RequirementType, RequirementSource
from app.services.auth_service import hash_password


def auto_seed_db():
    """Automatically seeds default demo accounts and a sample project if empty."""
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        if not db.query(User).filter(User.email == "pm@scopesentinel.com").first():
            print("[Auto-Seed] Seeding demo users and initial project...")
            pm = User(
                name="Rahul Sharma",
                email="pm@scopesentinel.com",
                hashed_password=hash_password("password123"),
                role=UserRole.pm,
            )
            dev = User(
                name="Priya Patel",
                email="dev@scopesentinel.com",
                hashed_password=hash_password("password123"),
                role=UserRole.developer,
            )
            qa = User(
                name="Amit Singh",
                email="qa@scopesentinel.com",
                hashed_password=hash_password("password123"),
                role=UserRole.qa,
            )
            db.add_all([pm, dev, qa])
            db.commit()

            project = Project(
                name="College Management System",
                description="Full-stack system for managing students, courses, and attendance",
                github_repo_url="https://github.com/demo/college-management",
                sprint_end_date=datetime.utcnow() + timedelta(days=14),
                team_size=5,
            )
            db.add(project)
            db.commit()

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
                db.add(
                    Requirement(
                        project_id=project.id,
                        text=t,
                        type=RequirementType.functional,
                        source=RequirementSource.document,
                        confidence_score=0.95,
                    )
                )
            db.commit()
            print("[Auto-Seed] Successfully created default users and requirements!")
        db.close()
    except Exception as e:
        print(f"[Auto-Seed Error] {e}")


# Run table creation & auto-seed on module startup
auto_seed_db()

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="ScopeSentinel API",
    description="AI Requirement Guardian & GitHub Engineering Intelligence Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS — allows React frontend to call the API ──────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.requirements import router as requirements_router
from app.api.changes import router as changes_router
from app.api.upload import router as upload_router
from app.api.search import router as search_router
from app.api.impact import router as impact_router
from app.api.analytics import router as analytics_router
from app.api.agent import router as agent_router
from app.api.github import router as github_router
from app.api.pr_review import router as pr_review_router
from app.api.jira import router as jira_router
from app.api.email import router as email_router

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(requirements_router)
app.include_router(changes_router)
app.include_router(upload_router)
app.include_router(search_router)
app.include_router(impact_router)
app.include_router(analytics_router)
app.include_router(agent_router)
app.include_router(github_router)
app.include_router(pr_review_router)
app.include_router(jira_router)
app.include_router(email_router)


# ── Health & Seed Endpoints ────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "project": "ScopeSentinel v2.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


@app.get("/seed", tags=["Health"])
def manual_seed():
    auto_seed_db()
    return {"status": "success", "message": "Database seeded with demo users & project"}
