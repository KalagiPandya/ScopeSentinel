"""
ScopeSentinel GitHub Intelligence Pipeline.

    START -> github_intel (Agent 3) -> coverage (Agent 4) -> END

Agent 3 scans the GitHub repository and builds a file-classification summary.
Agent 4 takes that summary + a list of project requirements and estimates
a Requirement Coverage Score for each one.

This is a SEPARATE graph from the main change-detection pipeline
(agent/graph.py) because it operates on a whole repo + requirement list,
not a single text snippet.
"""
from app.agent.state import AgentState
from app.agent.nodes.github_intel import github_intel_node
from app.agent.nodes.coverage import coverage_node


def build_github_graph():
    from langgraph.graph import StateGraph, END

    graph = StateGraph(AgentState)
    graph.add_node("github_intel", github_intel_node)
    graph.add_node("coverage", coverage_node)

    graph.set_entry_point("github_intel")
    graph.add_edge("github_intel", "coverage")
    graph.add_edge("coverage", END)

    return graph.compile()


def run_github_pipeline(
    project_id: str,
    repo_url: str,
    requirements_to_check: list,
    github_token: str | None = None,
) -> AgentState:
    """
    Runs Agent 3 (repo scan) + Agent 4 (coverage scoring).

    requirements_to_check: list of {"id": str, "text": str}

    Returns final AgentState with:
      - repo_summary: file classification, README, commits
      - coverage_results: list of CoverageResult (one per requirement)
    """
    app = build_github_graph()

    initial_state: AgentState = {
        "project_id": project_id,
        "repo_url": repo_url,
        "github_token": github_token,
        "requirements_to_check": requirements_to_check,
        "repo_summary": None,
        "coverage_results": [],
        "errors": [],
        "status": "pending",
    }

    return app.invoke(initial_state)
