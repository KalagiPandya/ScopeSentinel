"""
Agent 2 — Requirement Drift Detector

Takes the requirements extracted by Agent 1 and checks each one against
the existing requirement baseline (stored in Qdrant) using semantic
similarity search.

Classifies each as:
  - no_change    : already exists (similarity >= 0.92)
  - modification : existing requirement was reworded (0.60 - 0.92)
  - new_addition : brand new requirement (< 0.60)
"""
from app.agent.state import AgentState, DetectedChange
from app.services.change_detection_service import detect_change


def detector_node(state: AgentState) -> AgentState:
    """
    LangGraph node — Agent 2.
    Reads state['extracted_requirements'], writes state['detected_changes'].

    Only includes requirements that represent an actual CHANGE
    (skips no_change — those are already known).
    """
    project_id = state.get("project_id", "")
    extracted = state.get("extracted_requirements", [])
    errors = state.get("errors", [])

    if not project_id:
        return {
            **state,
            "detected_changes": [],
            "status": "error",
            "errors": errors + ["detector_node: project_id is missing"],
        }

    if not extracted:
        return {
            **state,
            "detected_changes": [],
            "status": "done",
        }

    changes: list[DetectedChange] = []
    new_errors = list(errors)

    for req in extracted:
        text = req["text"]
        try:
            result = detect_change(new_text=text, project_id=project_id)
            if result["change_type"] != "no_change":
                changes.append({
                    "new_text": text,
                    "change_type": result["change_type"],
                    "similarity_score": result["similarity_score"],
                    "similar_requirement": result.get("similar_requirement"),
                    "word_diff": result.get("word_diff"),
                })
        except Exception as e:
            new_errors.append(f"detector_node: failed on '{text[:50]}...': {str(e)}")

    return {
        **state,
        "detected_changes": changes,
        "status": "done",
        "errors": new_errors,
    }
