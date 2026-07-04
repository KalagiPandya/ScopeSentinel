"""
ScopeSentinel PR Compliance Review Pipeline.

    START -> pr_reviewer (Agent 7) -> END

Single-node pipeline (kept as a graph for consistency and easy extension —
e.g. adding a "post_comment" node later that calls the GitHub API).
"""
from app.agent.state import AgentState
from app.agent.nodes.pr_reviewer import pr_reviewer_node


def build_pr_graph():
    from langgraph.graph import StateGraph, END

    graph = StateGraph(AgentState)
    graph.add_node("pr_reviewer", pr_reviewer_node)

    graph.set_entry_point("pr_reviewer")
    graph.add_edge("pr_reviewer", END)

    return graph.compile()


def run_pr_review(
    pr_title: str,
    pr_body: str,
    pr_changed_files: list,
    project_requirements: list,
) -> AgentState:
    """
    Runs Agent 7 on a single PR.

    pr_changed_files: list of file path strings
    project_requirements: list of {"id": str, "text": str}

    Returns final AgentState with state['pr_review']:
      {
        "matched_requirements": [...],
        "compliance_score": 0-100,
        "missing_items": [...],
        "recommendation": "approve|request_changes|comment_only",
        "summary": "...",
        "comment_markdown": "..."
      }
    """
    app = build_pr_graph()

    initial_state: AgentState = {
        "pr_title": pr_title,
        "pr_body": pr_body,
        "pr_changed_files": pr_changed_files,
        "project_requirements": project_requirements,
        "pr_review": None,
        "errors": [],
        "status": "pending",
    }

    return app.invoke(initial_state)
