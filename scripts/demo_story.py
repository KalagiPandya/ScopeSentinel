"""
Day 18 Demo — The Complete ScopeSentinel Story (Interview-Ready)

This script walks through the EXACT scenario from your SRS, end to end,
printing a narrated story you can read aloud during a demo or interview.

Scenario recap:
  Week 1: SRS says "Students login with email + password"
  Week 3: Client casually mentions in a meeting: "add OTP too"
  -> ScopeSentinel catches it same day, scores the risk, tells the team
     which modules are affected, and (if a repo is connected) tells you
     whether the code actually implements it yet.

REQUIRES: OPENAI_API_KEY set to a real key in .env

Run from the root ScopeSentinel/ folder:
    python scripts/demo_story.py
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models.project import Project
from app.agent.graph import run_pipeline


def banner(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def beat(text, pause=0.4):
    print(f"\n>> {text}")
    time.sleep(pause)


db = SessionLocal()
project = db.query(Project).filter(Project.name == "College Management System").first()
if not project:
    print("Project not found. Run scripts/seed.py first.")
    db.close()
    sys.exit(1)

banner("SCOPESENTINEL — END-TO-END DEMO STORY")
print(f"Project: {project.name}")

beat("WEEK 1 — Original requirement on file (from seed data):")
print('  "The system must support OTP verification during student login"')

beat("WEEK 3 — A client call happens. Nobody updates the SRS by hand.")
print("  Instead, the meeting recording/transcript is dropped into ScopeSentinel.")

transcript = """
Quick recap from today's call with the client.

They confirmed the login flow needs email, password, AND OTP verification -
this is now a hard requirement from their compliance team, not optional.
They also want OTP to expire after 5 minutes for security.

Separately, the finance team asked if students can get an SMS reminder
3 days before fees are due - this is a brand new ask, wasn't discussed before.
"""

beat("Feeding this transcript into the ScopeSentinel pipeline (Agents 1,2,5,6,8)...")
print(transcript.strip())

result = run_pipeline(project_id=str(project.id), raw_text=transcript, source="meeting")

if result.get("errors"):
    print("\n[warnings]", result["errors"])

beat("AGENT 1 (Extractor) found these requirement statements:")
for i, r in enumerate(result.get("extracted_requirements", []), 1):
    print(f"  {i}. {r['text']}  (confidence {r['confidence']:.0%})")

beat("AGENT 2 (Drift Detector) classified each one against the existing baseline:")
for c in result.get("detected_changes", []):
    print(f"\n  -> {c['change_type'].upper()}  (similarity {c['similarity_score']:.0%})")
    print(f"     \"{c['new_text']}\"")
    if c.get("similar_requirement"):
        print(f"     closest existing: \"{c['similar_requirement']['text']}\"")

beat("AGENT 5 (Impact Analyzer) ran BFS on the Neo4j graph for each change:")
for c in result.get("detected_changes", []):
    impact = c.get("impact", {})
    affected = impact.get("total_affected", 0)
    names = [m["name"] for m in impact.get("depth_1", [])]
    print(f"  - \"{c['new_text'][:50]}...\" affects {affected} module(s): {', '.join(names) or 'none in graph yet'}")

beat("AGENT 6 (Risk Scorer) calculated risk for each change:")
for c in result.get("detected_changes", []):
    risk = c.get("risk", {})
    print(f"  - {risk.get('risk_level', '?').upper()} ({risk.get('risk_score', 0)}/100)")
    print(f"    {risk.get('justification', '')}")
    print(f"    Recommended action: {risk.get('recommended_action', '')}")

beat("AGENT 8 (Notifier) decided who to alert:")
for n in result.get("notifications", []):
    print(f"  - Change #{n['change_index']}: {n['risk_level']} risk -> notified via {', '.join(n['sent_channels'])}")

banner("THIS IS THE CORE VALUE PROPOSITION")
print("""
Without ScopeSentinel:
  The OTP-expiry detail and the new SMS reminder requirement would have
  stayed buried in a call recording. Two weeks later, a developer ships
  OTP without expiry. QA doesn't test for it because it's not in Jira.
  The client finds out in UAT. Rework costs days and trust.

With ScopeSentinel:
  Both changes were caught the same day, classified, risk-scored, mapped
  to affected modules, and routed to the right people automatically -
  before a single line of wrong code was written.
""")

beat("Now imagine connecting this to GitHub (Agents 3 & 4)...")
print("""
  scripts/test_coverage_pipeline.py shows the next step: scanning the
  actual repository and answering "was this requirement ACTUALLY
  implemented in code?" - not just "is it tracked somewhere?"

  That question is what makes ScopeSentinel a requirement-to-code
  traceability platform, not just another monitoring dashboard.
""")

banner("END OF DEMO STORY")
db.close()
