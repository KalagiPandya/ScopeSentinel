"""
Jira integration (Agent 1 input source).

Fetches real issues from a Jira Cloud project via the REST API v3 and
turns each one into a plain-text blob (summary + description + recent
comments) that Agent 1 (Extractor) can read exactly like a pasted
meeting transcript or email.

Auth: Jira Cloud uses HTTP Basic auth with your account email + an API
token (NOT your password). Generate a token at:
https://id.atlassian.com/manage-profile/security/api-tokens

Docs: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
"""
import httpx
from app.config import settings


class JiraNotConfigured(Exception):
    pass


def _client() -> httpx.Client:
    if not (settings.JIRA_BASE_URL and settings.JIRA_EMAIL and settings.JIRA_API_TOKEN):
        raise JiraNotConfigured(
            "Jira is not configured. Set JIRA_BASE_URL, JIRA_EMAIL, and "
            "JIRA_API_TOKEN in your .env file. Generate a token at "
            "https://id.atlassian.com/manage-profile/security/api-tokens"
        )
    return httpx.Client(
        base_url=settings.JIRA_BASE_URL.rstrip("/"),
        auth=(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN),
        headers={"Accept": "application/json"},
        timeout=30.0,
    )


def test_connection() -> dict:
    """Quick sanity check — confirms the credentials actually work."""
    with _client() as client:
        resp = client.get("/rest/api/3/myself")
        resp.raise_for_status()
        data = resp.json()
        return {"connected": True, "account": data.get("displayName"), "email": data.get("emailAddress")}


def _adf_to_text(node) -> str:
    """Jira v3 description/comments are Atlassian Document Format (nested
    JSON), not plain text. Walk the tree and pull out the text runs."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    parts = []
    if isinstance(node, dict):
        if node.get("type") == "text":
            parts.append(node.get("text", ""))
        for child in node.get("content", []) or []:
            parts.append(_adf_to_text(child))
    elif isinstance(node, list):
        for child in node:
            parts.append(_adf_to_text(child))
    return " ".join(p for p in parts if p)


def fetch_issues(project_key: str = None, jql: str = None, max_results: int = 25) -> list[dict]:
    """
    Fetch issues from Jira and return each as
    {"key": "SCOPE-12", "text": "<summary + description + comments>"}

    Pass either project_key (fetches that project's recently updated
    issues) or a custom jql string for full control.
    """
    key = project_key or settings.JIRA_PROJECT_KEY
    if not jql:
        if not key:
            raise JiraNotConfigured(
                "No project_key given and JIRA_PROJECT_KEY is not set in .env"
            )
        jql = f'project = "{key}" ORDER BY updated DESC'

    with _client() as client:
        resp = client.get(
            "/rest/api/3/search",
            params={
                "jql": jql,
                "maxResults": max_results,
                "fields": "summary,description,comment",
            },
        )
        resp.raise_for_status()
        payload = resp.json()

    issues = []
    for issue in payload.get("issues", []):
        fields = issue.get("fields", {})
        summary = fields.get("summary", "") or ""
        description = _adf_to_text(fields.get("description"))

        comments = []
        for c in (fields.get("comment", {}) or {}).get("comments", [])[-5:]:
            comments.append(_adf_to_text(c.get("body")))

        text = summary
        if description:
            text += f"\n\n{description}"
        if comments:
            text += "\n\nComments:\n" + "\n".join(f"- {c}" for c in comments if c)

        issues.append({"key": issue.get("key"), "text": text.strip()})

    return issues
