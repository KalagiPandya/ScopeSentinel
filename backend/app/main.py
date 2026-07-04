from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import models so SQLAlchemy registers all tables
from app.database import engine, Base
from app import models  # noqa: F401 — side-effect import
from app.config import settings

# Create all DB tables on startup (safe — skips existing tables)
Base.metadata.create_all(bind=engine)

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="ScopeSentinel API",
    description="AI Requirement Guardian & GitHub Engineering Intelligence Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS — allows React frontend (localhost:5173 / 3000) to call the API ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
from app.api.auth        import router as auth_router
from app.api.projects    import router as projects_router
from app.api.requirements import router as requirements_router
from app.api.changes     import router as changes_router
from app.api.upload      import router as upload_router
from app.api.search      import router as search_router
from app.api.impact      import router as impact_router
from app.api.analytics   import router as analytics_router
from app.api.agent       import router as agent_router
from app.api.github      import router as github_router
from app.api.pr_review   import router as pr_review_router

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


# ── Health ─────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "project": "ScopeSentinel v2.0",
        "status":  "running",
        "docs":    "http://localhost:8000/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
