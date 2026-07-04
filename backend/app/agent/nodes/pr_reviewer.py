"""
Agent 7 — Pull Request Compliance Reviewer

Triggered when a GitHub PR is opened/updated (via webhook) or manually
via API. Given the PR's changed files and the project's requirements,
the LLM checks:

  - Which requirement(s) does this PR likely relate to?
  - Is the implementation complete, or is something missing?
  - Any obvious security/quality concerns based on file names + diff stats?

Output is designed to be postable as a GitHub PR review comment.
"""
import json
from typing import List, Dict
from app.agent.state import AgentState


PR_REVIEW_PROMPT = """You are an AI code reviewer for a software team using
ScopeSentinel, a requirement-tracking platform. A Pull Request was opened.

PULL REQUEST INFO:
Title: {pr_title}
Description: {pr_body}

CHANGED FILES ({file_count} files):
{changed_files}

PROJECT REQUIREMENTS (most likely related to this PR):
{requirements}

Your task:
1. Identify which requirement(s) from the list above this PR appears to address
   (match by keywords/topic — e.g. "otp", "login", "marksheet")
2. Estimate a compliance_score (0-100): how completely does this PR seem to
   implement the matched requirement(s), based on file names and PR description?
3. List specific missing_items if the implementation looks incomplete
   (e.g. "No test file added for this change", "No frontend component found for this API")
4. Give an overall recommendation: "approve" | "request_changes" | "comment_only"

Return ONLY valid JSON, no markdown:
{{
  "matched_requirements": ["<requirement text 1>", "..."],
  "compliance_score": <integer 0-100>,
  "missing_items": ["...", "..."],
  "recommendation": "approve|request_changes|comment_only",
  "summary": "<2-3 sentence plain English review summary>"
}}

If no requirements seem related, matched_requirements should be an empty list
and recommendation should be "comment_only".
"""


def _call_llm(prompt: str) -> str:
    from openai import OpenAI
    from app.config import settings

    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {}


def _format_requirements(requirements: List[Dict]) -> str:
    if not requirements:
        return "  (no requirements found for this project)"
    lines = []
    for r in requirements[:30]:  # cap to keep prompt small
        lines.append(f"  - {r['text']}")
    return "\n".join(lines)


def _format_files(files: List[str]) -> str:
    if not files:
        return "  (no files listed)"
    return "\n".join(f"  - {f}" for f in files[:50])


def pr_reviewer_node(state: AgentState) -> AgentState:
    """
    Reads from state:
      - pr_title: str
      - pr_body: str
      - pr_changed_files: List[str]
      - project_requirements: List[{"id","text"}]

    Writes state['pr_review']:
      {
        "matched_requirements": [...],
        "compliance_score": 0-100,
        "missing_items": [...],
        "recommendation": "approve|request_changes|comment_only",
        "summary": "...",
        "comment_markdown": "<formatted GitHub comment>"
      }
    """
    errors = list(state.get("errors", []))

    pr_title = state.get("pr_title", "")
    pr_body = state.get("pr_body", "") or "(no description)"
    changed_files = state.get("pr_changed_files", [])
    requirements = state.get("project_requirements", [])

    try:
        prompt = PR_REVIEW_PROMPT.format(
            pr_title=pr_title,
            pr_body=pr_body,
            file_count=len(changed_files),
            changed_files=_format_files(changed_files),
            requirements=_format_requirements(requirements),
        )
        raw = _call_llm(prompt)
        parsed = _parse_json(raw)

        if not parsed:
            raise ValueError("LLM returned unparseable response")

        matched = parsed.get("matched_requirements", []) or []
        score = int(max(0, min(100, parsed.get("compliance_score", 0))))
        missing = parsed.get("missing_items", []) or []
        recommendation = parsed.get("recommendation", "comment_only")
        if recommendation not in ("approve", "request_changes", "comment_only"):
            recommendation = "comment_only"
        summary = parsed.get("summary", "")

    except Exception as e:
        matched, score, missing, recommendation, summary = (
            [], 0, ["Review analysis failed"], "comment_only", "Automated review could not be completed."
        )
        errors.append(f"pr_reviewer_node: {str(e)}")

    # Build a GitHub-comment-ready markdown block
    comment_lines = ["## 🛡️ ScopeSentinel AI Review", ""]
    if matched:
        comment_lines.append("**Matched Requirement(s):**")
        for m in matched:
            comment_lines.append(f"- {m}")
        comment_lines.append("")
    comment_lines.append(f"**Compliance Score:** {score}/100")
    comment_lines.append("")
    if missing:
        comment_lines.append("**Missing / To Review:**")
        for m in missing:
            comment_lines.append(f"- ⚠️ {m}")
        comment_lines.append("")
    comment_lines.append(f"**Summary:** {summary}")
    comment_lines.append("")
    comment_lines.append(f"_Recommendation: `{recommendation}`_")

    pr_review = {
        "matched_requirements": matched,
        "compliance_score": score,
        "missing_items": missing,
        "recommendation": recommendation,
        "summary": summary,
        "comment_markdown": "\n".join(comment_lines),
    }

    return {**state, "pr_review": pr_review, "status": "done", "errors": errors}
