"""
Day 8 Demo — Test the GitHub Coverage Pipeline (Agents 3 & 4)

This is THE signature feature of ScopeSentinel:
  "A requirement changed. Did the code ACTUALLY implement it?"

This script:
  1. Connects to a real public GitHub repo (Agent 3 scans it)
  2. Takes your seeded requirements
  3. Agent 4 estimates a Coverage Score for each one

REQUIRES: OPENAI_API_KEY set to a real key in .env

By default this uses a small public demo repo. You can change
DEMO_REPO_URL to your OWN repository once you start coding ScopeSentinel
itself — then it will analyze coverage of YOUR requirements against
YOUR code!

Run from the root ScopeSentinel/ folder:
    python scripts/test_coverage_pipeline.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models.project import Project
from app.models.requirement import Requirement
from app.agent.github_graph import run_github_pipeline

# Change this to your own repo once you start building!
DEMO_REPO_URL = "https://github.com/tiangolo/full-stack-fastapi-template"

db = SessionLocal()

project = db.query(Project).filter(Project.name == "College Management System").first()
if not project:
    print("Project not found. Run seed.py first.")
    db.close()
    sys.exit(1)

# Just test with the first 3 requirements (to keep API calls low)
requirements = db.query(Requirement).filter(
    Requirement.project_id == project.id
).limit(3).all()

print(f"Project: {project.name}")
print(f"Scanning repo: {DEMO_REPO_URL}")
print(f"Checking coverage for {len(requirements)} requirement(s)...\n")
print("=" * 65)

requirements_to_check = [{"id": str(r.id), "text": r.text} for r in requirements]

result = run_github_pipeline(
    project_id=str(project.id),
    repo_url=DEMO_REPO_URL,
    requirements_to_check=requirements_to_check,
)

if result.get("errors"):
    print("ERRORS:")
    for e in result["errors"]:
        print(f"  - {e}")
    print()

repo_summary = result.get("repo_summary")
if repo_summary:
    print(f"AGENT 3 - Repository Scan Results:")
    print("-" * 65)
    print(f"  Repo: {repo_summary['repo_name']}")
    print(f"  Description: {repo_summary['description']}")
    print(f"  Total files scanned: {repo_summary['total_files']}")
    print(f"  File breakdown: {repo_summary['file_counts']}")
    print(f"\n  Recent commits:")
    for c in repo_summary['recent_commits'][:3]:
        print(f"    {c['sha']} - {c['message']}")

print(f"\nAGENT 4 - Requirement Coverage Scores:")
print("-" * 65)

for cov in result.get("coverage_results", []):
    pct = cov["coverage_percent"]
    bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
    print(f"\n  Requirement: {cov['requirement_text'][:70]}")
    print(f"  Coverage: [{bar}] {pct}%")
    if cov["found_implementations"]:
        print(f"  Found:")
        for f in cov["found_implementations"]:
            print(f"    + {f}")
    if cov["missing_implementations"]:
        print(f"  Missing:")
        for m in cov["missing_implementations"]:
            print(f"    - {m}")

print("\n" + "=" * 65)
print("This is exactly what POST /github/scan-coverage does via the API,")
print("plus it saves results to the coverage_scores table for the")
print("Coverage Center dashboard.")
print("=" * 65)

db.close()
