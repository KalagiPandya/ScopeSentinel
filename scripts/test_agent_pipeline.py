"""
Day 5 Demo — Test the Agent Pipeline (Agents 1 & 2)

This simulates the EXACT scenario from the SRS:
  Week 1: "Students login with email + password"  (already in baseline)
  Week 3: Client says in a meeting: "Add OTP for security"

This script feeds that meeting transcript into the pipeline and shows:
  1. Agent 1 extracting the requirement from natural conversation
  2. Agent 2 detecting it's a MODIFICATION of the existing login requirement
  3. The word-level diff showing exactly what changed

REQUIRES: OPENAI_API_KEY set to a real key in .env

Run from the root ScopeSentinel/ folder:
    python scripts/test_agent_pipeline.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models.project import Project
from app.agent.graph import run_pipeline

db = SessionLocal()

project = db.query(Project).filter(Project.name == "College Management System").first()
if not project:
    print("Project not found. Run seed.py first.")
    db.close()
    sys.exit(1)

print(f"Project: {project.name}  (id={project.id})")
print("=" * 60)

# Simulated meeting transcript (Week 3 scenario from the SRS)
meeting_transcript = """
Alright team, quick update from today's client call.

The client is happy with progress overall. One important thing though -
they want us to add OTP verification when students log in, on top of the
existing email and password. This is for security since some parents
complained about account sharing.

Also, just a reminder - the dashboard should still load within 2 seconds,
that hasn't changed. And don't forget the marksheet PDF download feature,
that's still on track for next sprint.

Oh and one more thing - faculty should be able to see a history of all
leave applications they've approved or rejected, not just pending ones.
That's a new ask from the HOD.
"""

print("\nMEETING TRANSCRIPT:")
print(meeting_transcript)
print("=" * 60)
print("\nRunning Agent Pipeline (Extractor -> Detector)...\n")

result = run_pipeline(
    project_id=str(project.id),
    raw_text=meeting_transcript,
    source="meeting",
)

if result.get("errors"):
    print("ERRORS:")
    for e in result["errors"]:
        print(f"  - {e}")
    print()

print(f"Status: {result['status']}")
print(f"\nAGENT 1 - Extracted {len(result['extracted_requirements'])} requirement(s):")
print("-" * 60)
for i, req in enumerate(result["extracted_requirements"], 1):
    print(f"  {i}. [{req['type']}] (confidence {req['confidence']:.2f})")
    print(f"     {req['text']}")

print(f"\nAGENT 2 - Detected {len(result['detected_changes'])} change(s):")
print("-" * 60)
for i, change in enumerate(result["detected_changes"], 1):
    print(f"\n  Change {i}: {change['change_type'].upper()}")
    print(f"  New text: {change['new_text']}")
    print(f"  Similarity to existing: {change['similarity_score']:.2%}")

    if change["similar_requirement"]:
        print(f"  Closest existing requirement:")
        print(f"     '{change['similar_requirement']['text']}'")

    if change["word_diff"]:
        print(f"  Word diff: {change['word_diff']['formatted']}")
        print(f"  Words added:   {change['word_diff']['added_words']}")
        print(f"  Words removed: {change['word_diff']['removed_words']}")

print("\n" + "=" * 60)
print("Done! This is exactly what /agent/run does via the API,")
print("plus it saves new/modified requirements to PostgreSQL + Qdrant.")
print("=" * 60)

db.close()
