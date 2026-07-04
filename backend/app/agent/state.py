"""
AgentState — the shared "memory" object that flows through the LangGraph pipeline.

Every agent node reads from this state and writes its results back into it.
Think of it as a clipboard that gets passed from agent to agent.
"""
from typing import TypedDict, List, Optional, Dict, Any


class ExtractedRequirement(TypedDict):
    text: str
    type: str            # functional | non_functional | constraint
    confidence: float


class DetectedChange(TypedDict):
    new_text: str
    change_type: str            # no_change | modification | new_addition
    similarity_score: float
    similar_requirement: Optional[Dict[str, Any]]
    word_diff: Optional[Dict[str, Any]]


class CoverageResult(TypedDict):
    requirement_id: str
    requirement_text: str
    coverage_percent: int
    found_implementations: List[str]
    missing_implementations: List[str]


class NotificationResult(TypedDict):
    change_index: int
    risk_level: str
    channels: List[str]
    sent_channels: List[str]
    message: str


class PRReviewResult(TypedDict):
    matched_requirements: List[str]
    compliance_score: int
    missing_items: List[str]
    recommendation: str
    summary: str
    comment_markdown: str


class AgentState(TypedDict, total=False):
    # ── Input ──────────────────────────────────────────────────────────────
    project_id: str
    raw_text: str            # the input text (meeting transcript / email / doc)
    source: str               # meeting | email | document | jira | github_issue

    # ── Agent 1 output: Requirement Extractor ────────────────────────────────
    extracted_requirements: List[ExtractedRequirement]

    # ── Agent 2 output: Drift Detector ───────────────────────────────────────
    detected_changes: List[DetectedChange]

    # ── GitHub pipeline (Agents 3 & 4) ───────────────────────────────────────
    repo_url: str
    github_token: Optional[str]
    repo_summary: Optional[Dict[str, Any]]       # Agent 3 output
    requirements_to_check: List[Dict[str, str]]  # input to Agent 4: [{"id","text"}]
    coverage_results: List[CoverageResult]       # Agent 4 output

    # ── Agent 8 output: Notifications ────────────────────────────────────────
    notifications: List[NotificationResult]

    # ── PR Review pipeline (Agent 7) ─────────────────────────────────────────
    pr_title: str
    pr_body: str
    pr_changed_files: List[str]
    project_requirements: List[Dict[str, str]]
    pr_review: Optional[PRReviewResult]

    # ── Pipeline metadata ──────────────────────────────────────────────────
    errors: List[str]
    status: str               # pending | extracting | detecting | scanned | done | error
