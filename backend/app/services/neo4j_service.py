"""
Neo4j graph database service.
Stores requirement-module relationships.
Runs BFS (Breadth First Search) to find all modules affected by a requirement change.

Graph structure:
  (Module)-[:IMPLEMENTS]->(Requirement)
  (Module)-[:DEPENDS_ON]->(Module)
  (TestCase)-[:TESTS]->(Requirement)
"""
from typing import List, Dict
from app.config import settings


def _driver():
    from neo4j import GraphDatabase
    return GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )


def setup_constraints():
    """Run once at startup to create uniqueness indexes."""
    driver = _driver()
    with driver.session() as s:
        for q in [
            "CREATE CONSTRAINT req_id IF NOT EXISTS FOR (r:Requirement) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT mod_id IF NOT EXISTS FOR (m:Module) REQUIRE m.id IS UNIQUE",
        ]:
            try:
                s.run(q)
            except Exception:
                pass  # already exists
    driver.close()


def create_requirement_node(req_id: str, project_id: str, text: str):
    driver = _driver()
    with driver.session() as s:
        s.run(
            "MERGE (r:Requirement {id:$id}) SET r.project_id=$pid, r.text=$text",
            id=req_id, pid=project_id, text=text,
        )
    driver.close()


def create_module_node(module_id: str, project_id: str, name: str, module_type: str):
    """module_type: frontend | backend | database | api | test"""
    driver = _driver()
    with driver.session() as s:
        s.run(
            "MERGE (m:Module {id:$id}) SET m.project_id=$pid, m.name=$name, m.type=$type",
            id=module_id, pid=project_id, name=name, type=module_type,
        )
    driver.close()


def link_module_to_requirement(req_id: str, module_id: str):
    driver = _driver()
    with driver.session() as s:
        s.run(
            """
            MATCH (r:Requirement {id:$rid})
            MATCH (m:Module {id:$mid})
            MERGE (m)-[:IMPLEMENTS]->(r)
            """,
            rid=req_id, mid=module_id,
        )
    driver.close()


def bfs_impact(req_id: str, max_depth: int = 3) -> Dict:
    """
    BFS from a Requirement node outward.
    Finds all Modules that implement it (directly or indirectly).

    Returns:
      depth_1  -> modules that directly implement this requirement
      depth_2  -> modules that depend on depth_1 modules
      depth_3  -> test cases and distant modules
      all_affected -> flat list of everything found
      total_affected -> count
    """
    driver = _driver()
    result = {
        "depth_1": [], "depth_2": [], "depth_3": [],
        "all_affected": [], "total_affected": 0,
    }
    with driver.session() as s:
        records = s.run(
            """
            MATCH path = (r:Requirement {id:$rid})<-[:IMPLEMENTS|DEPENDS_ON|TESTS*1..3]-(m)
            RETURN m.id AS id, m.name AS name, m.type AS type, length(path) AS depth
            ORDER BY depth
            """,
            rid=req_id,
        )
        seen = set()
        for rec in records:
            key = rec["id"]
            if key in seen:
                continue
            seen.add(key)
            node = {"id": rec["id"], "name": rec["name"], "type": rec["type"]}
            depth_key = f"depth_{min(rec['depth'], 3)}"
            result[depth_key].append(node)
            result["all_affected"].append(node)

    result["total_affected"] = len(result["all_affected"])
    driver.close()
    return result


def get_project_graph_stats(project_id: str) -> Dict:
    driver = _driver()
    stats = {}
    with driver.session() as s:
        for label in ["Requirement", "Module"]:
            r = s.run(
                f"MATCH (n:{label} {{project_id:$pid}}) RETURN count(n) AS cnt",
                pid=project_id,
            )
            stats[label.lower() + "s"] = r.single()["cnt"]
    driver.close()
    return stats


def seed_sample_graph(project_id: str, requirements: List[dict]):
    """
    Build a sample Neo4j graph for the seeded project.
    Links requirements to modules based on keyword matching.
    requirements: list of {"id": str, "text": str}
    """
    driver = _driver()

    modules = [
        {"id": f"{project_id}_fe_auth",       "name": "Frontend Auth Module",      "type": "frontend"},
        {"id": f"{project_id}_be_auth",        "name": "Backend Auth API",          "type": "backend"},
        {"id": f"{project_id}_db_users",       "name": "Users DB Table",            "type": "database"},
        {"id": f"{project_id}_fe_dashboard",   "name": "Frontend Dashboard",        "type": "frontend"},
        {"id": f"{project_id}_be_attendance",  "name": "Attendance API",            "type": "backend"},
        {"id": f"{project_id}_db_attendance",  "name": "Attendance DB Table",       "type": "database"},
        {"id": f"{project_id}_test_auth",      "name": "Auth Test Suite",           "type": "test"},
        {"id": f"{project_id}_fe_marksheet",   "name": "Marksheet Download Page",   "type": "frontend"},
        {"id": f"{project_id}_be_marks",       "name": "Marks API",                 "type": "backend"},
        {"id": f"{project_id}_be_email",       "name": "Email Notification Service","type": "backend"},
    ]

    keyword_map = {
        "login":      [f"{project_id}_fe_auth", f"{project_id}_be_auth",
                       f"{project_id}_db_users", f"{project_id}_test_auth"],
        "otp":        [f"{project_id}_fe_auth", f"{project_id}_be_auth"],
        "register":   [f"{project_id}_fe_auth", f"{project_id}_be_auth", f"{project_id}_db_users"],
        "attendance": [f"{project_id}_fe_dashboard", f"{project_id}_be_attendance",
                       f"{project_id}_db_attendance"],
        "mark":       [f"{project_id}_fe_marksheet", f"{project_id}_be_marks"],
        "download":   [f"{project_id}_fe_marksheet", f"{project_id}_be_marks"],
        "dashboard":  [f"{project_id}_fe_dashboard"],
        "email":      [f"{project_id}_be_email", f"{project_id}_be_auth"],
        "notification":[f"{project_id}_be_email"],
        "audit":      [f"{project_id}_be_auth"],
        "role":       [f"{project_id}_be_auth", f"{project_id}_db_users"],
        "encrypt":    [f"{project_id}_db_users"],
        "leave":      [f"{project_id}_fe_dashboard", f"{project_id}_be_attendance"],
    }

    with driver.session() as s:
        # Create module nodes
        for mod in modules:
            s.run(
                "MERGE (m:Module {id:$id}) SET m.project_id=$pid, m.name=$name, m.type=$type",
                id=mod["id"], pid=project_id, name=mod["name"], type=mod["type"],
            )

        # Create requirement nodes + link to modules
        for req in requirements:
            s.run(
                "MERGE (r:Requirement {id:$id}) SET r.project_id=$pid, r.text=$text",
                id=req["id"], pid=project_id, text=req["text"],
            )
            linked = set()
            text_lower = req["text"].lower()
            for kw, mids in keyword_map.items():
                if kw in text_lower:
                    linked.update(mids)
            for mid in linked:
                s.run(
                    """
                    MATCH (r:Requirement {id:$rid})
                    MATCH (m:Module {id:$mid})
                    MERGE (m)-[:IMPLEMENTS]->(r)
                    """,
                    rid=req["id"], mid=mid,
                )

    driver.close()
    print(f"Neo4j graph seeded for project {project_id}")
