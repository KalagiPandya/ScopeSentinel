"""
Qdrant embedding script — run AFTER seed.py.
Converts all requirement texts to vectors and stores them in Qdrant.
Enables semantic search and change detection.

REQUIRES: OPENAI_API_KEY set to a real key in your .env

Run from the root ScopeSentinel/ folder:
    python scripts/embed_requirements.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models.requirement import Requirement
from app.services.qdrant_service import create_collection_if_not_exists, store_requirement

db = SessionLocal()

print("Setting up Qdrant collection...")
create_collection_if_not_exists()

reqs = db.query(Requirement).all()
print(f"Embedding {len(reqs)} requirements...\n")

for i, req in enumerate(reqs, 1):
    point_id = store_requirement(
        requirement_id=str(req.id),
        project_id=str(req.project_id),
        text=req.text,
    )
    req.qdrant_point_id = point_id
    db.commit()
    print(f"  [{i:02d}/{len(reqs)}] {req.text[:65]}...")

print()
print("=" * 55)
print(f"Done! {len(reqs)} requirements embedded.")
print("  Verify: http://localhost:6333/dashboard")
print("=" * 55)
db.close()
