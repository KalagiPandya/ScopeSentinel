"""
Day 10 Demo — The Complete 8-Agent Pipeline

Part A: Run the main pipeline (Agents 1,2,5,6,8) on a meeting transcript.
         Shows extraction -> drift detection -> impact -> risk -> notification.

Part B: Run Agent 7 (PR Reviewer) on a simulated Pull Request.
         Shows requirement matching + compliance scoring.

REQUIRES: OPENAI_API_KEY set to a real key in .env
Part B additionally needs project.github_repo_url set (seed.py sets a
placeholder) — if PR fetch fails because the repo/PR doesn't exist,
Part B falls back to a LOCAL simulated PR (no GitHub call) so you can
still see Agent 7 working.

Run from the root ScopeSentinel/ folder:
    python scripts/test_full_pipeline.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models.project import Project
from app.models.requirement import Requirement
from app.agent.graph import run_pipeline
from app.agent.pr_graph import run_pr_review

db = SessionLocal()
project = db.query(Project).filter(Project.name == "College Management System").first()
if not project:
    print("Project not found. Run seed.py first.")
    db.close()
    sys.exit(1)

print("=" * 65)
print("PART A — Main Pipeline (Agents 1, 2, 5, 6, 8)")
print("=" * 65)

meeting_transcript = """
Quick update from the client call today. They want students to be able
to log in using email, password, AND OTP verification now - this is a
change from just email and password. Security requirement from their
compliance team.
"""

print("\nInput (meeting transcript):")
print(meeting_transcript.strip())
print("\nRunning pipeline...\n")

result = run_pipeline(
    project_id=str(project.id),
    raw_text=meeting_transcript,
    source="meeting",
)

if result.get("errors"):
    print("ERRORS:", result["errors"], "\n")

for i, change in enumerate(result.get("detected_changes", []), 1):
    print(f"Change {i}: {change['change_type'].upper()}")
    print(f"  Text: {change['new_text'][:80]}")
    print(f"  Similarity: {change['similarity_score']:.0%}")

    impact = change.get("impact", {})
    print(f"  Impact: {impact.get('total_affected', 0)} module(s) affected")
    for m in impact.get("depth_1", [])[:5]:
        print(f"    - {m['name']} ({m['type']})")

    risk = change.get("risk", {})
    print(f"  Risk: {risk.get('risk_score')}/100 ({risk.get('risk_level', '').upper()})")
    print(f"  Justification: {risk.get('justification', '')}")
    print(f"  Action: {risk.get('recommended_action', '')}")
    print()

for n in result.get("notifications", []):
    print(f"Notification (change {n['change_index']}): risk={n['risk_level']}, "
          f"channels={n['channels']}, sent={n['sent_channels']}")

print("\n" + "=" * 65)
print("PART B — PR Compliance Review (Agent 7)")
print("=" * 65)

requirements = db.query(Requirement).filter(Requirement.project_id == project.id).all()
project_requirements = [{"id": str(r.id), "text": r.text} for r in requirements]

# Simulated PR — no GitHub call needed, demonstrates Agent 7 directly
pr_title = "feat: add OTP verification to student login"
pr_body = "Implements OTP step after password login. Adds OTP input component and backend endpoint."
pr_changed_files = [
    "backend/app/api/auth.py",
    "backend/app/services/otp_service.py",
    "frontend/src/components/OTPInput.jsx",
    "frontend/src/pages/Login.jsx",
]

print(f"\nSimulated PR: \"{pr_title}\"")
print(f"Description: {pr_body}")
print(f"Changed files: {pr_changed_files}")
print("\nRunning Agent 7...\n")

pr_result = run_pr_review(
    pr_title=pr_title,
    pr_body=pr_body,
    pr_changed_files=pr_changed_files,
    project_requirements=project_requirements,
)

review = pr_result.get("pr_review", {})
print(f"Matched requirements:")
for m in review.get("matched_requirements", []):
    print(f"  - {m}")
print(f"\nCompliance score: {review.get('compliance_score')}/100")
print(f"Recommendation: {review.get('recommendation')}")
print(f"Summary: {review.get('summary')}")

if review.get("missing_items"):
    print(f"\nMissing items:")
    for m in review["missing_items"]:
        print(f"  - {m}")

print("\n--- GitHub comment that would be posted ---")
print(review.get("comment_markdown", ""))

print("\n" + "=" * 65)
print("All 8 agents demonstrated:")
print("  1. Extractor   2. Drift Detector   3. GitHub Intel (Day 7-8 demo)")
print("  4. Coverage Mapper (Day 7-8 demo)   5. Impact   6. Risk")
print("  7. PR Reviewer   8. Notifier")
print("=" * 65)

db.close()
