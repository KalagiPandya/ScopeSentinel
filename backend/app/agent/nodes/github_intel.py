"""
Agent 3 — GitHub Repository Intelligence

Scans a GitHub repository and builds a lightweight knowledge graph:
  - file tree classified by type (frontend/backend/database/test/config)
  - README content
  - recent commit messages

This is a standalone node (not part of the main change-detection graph)
because it operates on a whole repository rather than a single text input.
Called via the GitHub pipeline (see agent/github_graph.py).
"""
from app.agent.state import AgentState


def github_intel_node(state: AgentState) -> AgentState:
    """
    Reads state['repo_url'] and optional state['github_token'].
    Writes state['repo_summary'] with the scan results.
    """
    from app.services.github_service import scan_repository

    repo_url = state.get("repo_url", "")
    token = state.get("github_token")
    errors = list(state.get("errors", []))

    if not repo_url:
        return {**state, "repo_summary": None, "status": "error",
                "errors": errors + ["github_intel_node: repo_url is missing"]}

    try:
        summary = scan_repository(repo_url, token=token)
        return {**state, "repo_summary": summary, "status": "scanned"}
    except Exception as e:
        return {**state, "repo_summary": None, "status": "error",
                "errors": errors + [f"github_intel_node: {str(e)}"]}
