"""
ScopeSentinel Agent Pipeline — built with LangGraph.

Pipeline (Day 10 - complete change-detection chain):

    START -> extractor (Agent 1)
          -> detector  (Agent 2)
          -> impact    (Agent 5)
          -> risk      (Agent 6)
          -> notifier  (Agent 8)
          -> END

Agent 1 extracts requirement statements from raw text.
Agent 2 classifies each as no_change / modification / new_addition.
Agent 5 runs BFS on Neo4j to find affected modules for each change.
Agent 6 scores the risk (0-100) of each change using impact + similarity.
Agent 8 decides notification channels based on risk level and dispatches
  (or stubs) Slack/email alerts.

Agents 3 (GitHub Intelligence) and 4 (Coverage Mapper) run as a SEPARATE
pipeline (agent/github_graph.py) since they operate on a whole repository.

Agent 7 (PR Compliance Reviewer) also runs as a SEPARATE pipeline
(agent/pr_graph.py) since it's triggered by GitHub PR events, not by
arbitrary text input.
"""
from app.agent.state import AgentState
from app.agent.nodes.extractor import extractor_node
from app.agent.nodes.detector import detector_node
from app.agent.nodes.impact import impact_node
from app.agent.nodes.risk import risk_node
from app.agent.nodes.notifier import notifier_node


def build_graph():
    """Build and compile the main requirement-change pipeline."""
    from langgraph.graph import StateGraph, END

    graph = StateGraph(AgentState)

    graph.add_node("extractor", extractor_node)
    graph.add_node("detector", detector_node)
    graph.add_node("impact", impact_node)
    graph.add_node("risk", risk_node)
    graph.add_node("notifier", notifier_node)

    graph.set_entry_point("extractor")
    graph.add_edge("extractor", "detector")
    graph.add_edge("detector", "impact")
    graph.add_edge("impact", "risk")
    graph.add_edge("risk", "notifier")
    graph.add_edge("notifier", END)

    return graph.compile()


def run_pipeline(project_id: str, raw_text: str, source: str = "document") -> AgentState:
    """
    Runs the full Agents 1-2-5-6-8 pipeline on a piece of text.

    Returns final AgentState. Each item in detected_changes now has:
      - change_type, similarity_score, similar_requirement, word_diff
      - impact: {depth_1, depth_2, depth_3, total_affected}
      - risk:   {risk_score, risk_level, justification, recommended_action}

    state['notifications'] contains one entry per change:
      - channels: which channels SHOULD be notified based on risk
      - sent_channels: which were actually dispatched (or _stub if not configured)
    """
    app = build_graph()

    initial_state: AgentState = {
        "project_id": project_id,
        "raw_text": raw_text,
        "source": source,
        "extracted_requirements": [],
        "detected_changes": [],
        "errors": [],
        "status": "pending",
    }

    return app.invoke(initial_state)
