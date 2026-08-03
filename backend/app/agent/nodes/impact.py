"""
Agent 5 — Impact Analyzer

For each detected change (modification or new_addition), runs a BFS
traversal on the Neo4j graph starting from the closest matching
requirement node to find all affected modules.

If the requirement has no matching node in Neo4j yet (brand new),
impact is empty — that's expected and handled gracefully.
"""
from app.agent.state import AgentState


def impact_node(state: AgentState) -> AgentState:
    """
    LangGraph node — Agent 5.
    Reads state['detected_changes'], adds 'impact' key to each change dict.

    impact = {
        "depth_1": [...], "depth_2": [...], "depth_3": [...],
        "total_affected": N
    }
    """
    from app.services.neo4j_service import bfs_impact

    changes = state.get("detected_changes", [])
    errors = list(state.get("errors", []))

    for change in changes:
        similar = change.get("similar_requirement")
        req_id = similar["requirement_id"] if similar else None

        if not req_id:
            # Brand new requirement — nothing in the graph yet to traverse
            change["impact"] = {
                "depth_1": [], "depth_2": [], "depth_3": [],
                "all_affected": [], "total_affected": 0,
            }
            continue

        try:
            change["impact"] = bfs_impact(req_id=req_id, max_depth=3)
        except Exception as e:
            change["impact"] = {
                "depth_1": [], "depth_2": [], "depth_3": [],
                "all_affected": [], "total_affected": 0,
            }
            errors.append(f"impact_node: failed for req {req_id}: {str(e)}")

    return {**state, "detected_changes": changes, "errors": errors}
