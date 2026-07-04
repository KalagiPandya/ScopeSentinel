"""
ScopeSentinel MCP Server

Exposes ScopeSentinel's backend API as MCP tools so Claude Desktop (or any
MCP client) can directly:
  - list projects and requirements
  - run the AI agent pipeline on meeting/email text
  - check requirement coverage against GitHub
  - run a PR compliance review
  - get analytics summaries

This server is a thin wrapper — it calls the FastAPI backend over HTTP.
The backend must be running (default: http://localhost:8000).

SETUP:
  1. cd mcp-server
  2. python -m venv venv && venv\\Scripts\\activate  (or source venv/bin/activate)
  3. pip install -r requirements.txt
  4. Set SCOPESENTINEL_API_URL, SCOPESENTINEL_EMAIL, SCOPESENTINEL_PASSWORD
     in mcp-server/.env (copy from .env.example)
  5. Add this server to Claude Desktop's config (see README section "Day 11")

The server logs in once at startup and caches the JWT token, refreshing
automatically if a request returns 401.
"""
import os
import asyncio
from typing import Optional, Any
import httpx
from dotenv import load_dotenv

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

load_dotenv()

API_URL = os.getenv("SCOPESENTINEL_API_URL", "http://localhost:8000")
EMAIL = os.getenv("SCOPESENTINEL_EMAIL", "pm@scopesentinel.com")
PASSWORD = os.getenv("SCOPESENTINEL_PASSWORD", "password123")

server = Server("scopesentinel")

_token: Optional[str] = None


async def _login(client: httpx.AsyncClient) -> str:
    global _token
    resp = await client.post(f"{API_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    resp.raise_for_status()
    _token = resp.json()["access_token"]
    return _token


async def _request(method: str, path: str, json: Optional[dict] = None) -> Any:
    """Make an authenticated request to the ScopeSentinel API, auto re-login on 401."""
    global _token
    async with httpx.AsyncClient(timeout=60.0) as client:
        if _token is None:
            await _login(client)

        headers = {"Authorization": f"Bearer {_token}"}
        resp = await client.request(method, f"{API_URL}{path}", json=json, headers=headers)

        if resp.status_code == 401:
            await _login(client)
            headers = {"Authorization": f"Bearer {_token}"}
            resp = await client.request(method, f"{API_URL}{path}", json=json, headers=headers)

        resp.raise_for_status()
        return resp.json()


# ── Tool definitions ─────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_projects",
            description="List all ScopeSentinel projects with their IDs, names, and GitHub repo URLs.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="list_requirements",
            description="List all requirements for a given project ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project UUID"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="run_requirement_pipeline",
            description=(
                "Run the full AI agent pipeline on a piece of text (meeting transcript, "
                "email, or document excerpt). Extracts requirements, detects changes vs "
                "the existing baseline, analyzes impact (Neo4j BFS), scores risk (0-100), "
                "and decides notification channels. Returns new/modified requirements with "
                "risk scores and affected modules."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project UUID"},
                    "text": {"type": "string", "description": "Meeting transcript, email, or document text"},
                    "source": {
                        "type": "string",
                        "description": "Source type",
                        "enum": ["meeting", "email", "document", "jira", "github_issue"],
                        "default": "meeting",
                    },
                },
                "required": ["project_id", "text"],
            },
        ),
        Tool(
            name="scan_github_coverage",
            description=(
                "Scan a GitHub repository and calculate a Requirement Coverage Score "
                "(0-100%) for every requirement in the project — showing what's "
                "implemented and what's missing in the actual code."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project UUID"},
                    "repo_url": {"type": "string", "description": "e.g. https://github.com/owner/repo"},
                    "github_token": {"type": "string", "description": "Optional PAT for private repos"},
                },
                "required": ["project_id", "repo_url"],
            },
        ),
        Tool(
            name="get_coverage_dashboard",
            description="Get the Requirement Coverage dashboard data for a project (overall %, fully/partially/not implemented counts).",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project UUID"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="run_pr_review",
            description=(
                "Run an AI compliance review on a GitHub Pull Request — checks which "
                "requirements it addresses, gives a compliance score (0-100), and lists "
                "missing items."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project UUID"},
                    "pr_number": {"type": "integer", "description": "GitHub PR number"},
                    "post_comment": {"type": "boolean", "default": False},
                },
                "required": ["project_id", "pr_number"],
            },
        ),
        Tool(
            name="get_project_summary",
            description="Get analytics summary for a project: total requirements, total changes, risk distribution, and coverage stats.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project UUID"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="get_recent_changes",
            description="Get the most recent requirement changes for a project, including risk scores and impact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project UUID"},
                },
                "required": ["project_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "list_projects":
            result = await _request("GET", "/projects/")

        elif name == "list_requirements":
            result = await _request("GET", f"/requirements/project/{arguments['project_id']}")

        elif name == "run_requirement_pipeline":
            result = await _request("POST", "/agent/run", json={
                "project_id": arguments["project_id"],
                "text": arguments["text"],
                "source": arguments.get("source", "meeting"),
            })

        elif name == "scan_github_coverage":
            result = await _request("POST", "/github/scan-coverage", json={
                "project_id": arguments["project_id"],
                "repo_url": arguments["repo_url"],
                "github_token": arguments.get("github_token"),
            })

        elif name == "get_coverage_dashboard":
            result = await _request("GET", f"/github/coverage/project/{arguments['project_id']}")

        elif name == "run_pr_review":
            result = await _request("POST", "/pr-review/run", json={
                "project_id": arguments["project_id"],
                "pr_number": arguments["pr_number"],
                "post_comment": arguments.get("post_comment", False),
            })

        elif name == "get_project_summary":
            result = await _request("GET", f"/analytics/project/{arguments['project_id']}/summary")

        elif name == "get_recent_changes":
            result = await _request("GET", f"/changes/project/{arguments['project_id']}")

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    except httpx.HTTPStatusError as e:
        return [TextContent(type="text", text=f"API error {e.response.status_code}: {e.response.text}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
