"""
Neo4j graph setup — run AFTER seed.py.
Creates Requirement + Module nodes, links them via IMPLEMENTS edges.
Enables BFS impact analysis.

Run from the root ScopeSentinel/ folder:
    python scripts/setup_neo4j.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models.project import Project
from app.models.requirement import Requirement
from app.services.neo4j_service import setup_constraints, seed_sample_graph

db = SessionLocal()

project = db.query(Project).filter(Project.name == "College Management System").first()
if not project:
    print("Project not found. Run seed.py first.")
    db.close()
    sys.exit(1)

reqs = db.query(Requirement).filter(Requirement.project_id == project.id).all()
print(f"Found {len(reqs)} requirements")

print("Creating Neo4j constraints...")
setup_constraints()

print("Building graph...")
seed_sample_graph(
    project_id=str(project.id),
    requirements=[{"id": str(r.id), "text": r.text} for r in reqs],
)

print()
print("=" * 55)
print("Neo4j graph ready!")
print("  Open : http://localhost:7474")
print("  Login: neo4j / scopepass123")
print("  Query: MATCH (m:Module)-[:IMPLEMENTS]->(r:Requirement)")
print("         RETURN m,r LIMIT 25")
print("=" * 55)
db.close()
