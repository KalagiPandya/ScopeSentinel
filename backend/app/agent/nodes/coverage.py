"""
Agent 4 — Requirement-to-Code Coverage Mapper  (THE signature feature)

For each requirement in the project, this agent checks the GitHub
repository's file list (from Agent 3's scan) and asks an LLM:

  "Given this requirement and this list of repo files (with paths),
   is this requirement implemented? What's covered, what's missing?"

Output per requirement:
  {
    "requirement_id": "...",
    "requirement_text": "...",
    "coverage_percent": 0-100,
    "found_implementations": ["...", "..."],
    "missing_implementations": ["...", "..."]
  }

We send the LLM a CONDENSED file list (paths only, grouped by type) rather
than full file contents — this keeps token usage low while still giving
the LLM enough signal (file/folder naming usually reveals intent, e.g.
"routes/otp.py", "components/OTPInput.jsx", "models/otp_table.py").
"""
import json
from typing import List, Dict
from app.agent.state import AgentState


COVERAGE_PROMPT = """You are a senior software engineer doing a code review.
You are given ONE requirement and a list of file paths in the project's
GitHub repository (grouped by type). Estimate how well this requirement
is implemented based on the file names/paths alone.

REQUIREMENT:
"{requirement_text}"

REPOSITORY FILES (grouped by type, path only):

Frontend files:
{frontend_files}

Backend files:
{backend_files}

Database files:
{database_files}

Test files:
{test_files}

Based on file naming and structure, estimate:
- coverage_percent: 0-100, how much of this requirement appears implemented
- found_implementations: short list of WHAT seems to exist (e.g. "Login API route found", "OTP frontend component found")
- missing_implementations: short list of WHAT seems to be missing (e.g. "No OTP expiry logic found", "No audit log table found")

Return ONLY valid JSON, no markdown:
{{
  "coverage_percent": <integer 0-100>,
  "found_implementations": ["...", "..."],
  "missing_implementations": ["...", "..."]
}}

If you genuinely cannot tell anything from file names, return coverage_percent: 0
with missing_implementations: ["No matching files found in repository"]
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


def _group_files_by_type(files: List[Dict], file_type: str, limit: int = 60) -> str:
    paths = [f["path"] for f in files if f["type"] == file_type][:limit]
    if not paths:
        return "  (none)"
    return "\n".join(f"  - {p}" for p in paths)


def coverage_node(state: AgentState) -> AgentState:
    """
    Reads state['repo_summary'] (from Agent 3) and state['requirements_to_check']
    (list of {"id": str, "text": str}).

    Writes state['coverage_results'] — one entry per requirement.
    """
    repo_summary = state.get("repo_summary")
    requirements = state.get("requirements_to_check", [])
    errors = list(state.get("errors", []))

    if not repo_summary:
        return {**state, "coverage_results": [], "status": "error",
                "errors": errors + ["coverage_node: repo_summary is missing — run github_intel first"]}

    files = repo_summary.get("files", [])
    frontend_str = _group_files_by_type(files, "frontend")
    backend_str = _group_files_by_type(files, "backend")
    database_str = _group_files_by_type(files, "database")
    test_str = _group_files_by_type(files, "test")

    results = []
    for req in requirements:
        try:
            prompt = COVERAGE_PROMPT.format(
                requirement_text=req["text"],
                frontend_files=frontend_str,
                backend_files=backend_str,
                database_files=database_str,
                test_files=test_str,
            )
            raw = _call_llm(prompt)
            parsed = _parse_json(raw)

            coverage_percent = int(max(0, min(100, parsed.get("coverage_percent", 0))))
            found = parsed.get("found_implementations", []) or []
            missing = parsed.get("missing_implementations", []) or []

        except Exception as e:
            coverage_percent = 0
            found = []
            missing = ["Coverage analysis failed"]
            errors.append(f"coverage_node: failed for req {req.get('id')}: {str(e)}")

        results.append({
            "requirement_id": req["id"],
            "requirement_text": req["text"],
            "coverage_percent": coverage_percent,
            "found_implementations": found,
            "missing_implementations": missing,
        })

    return {**state, "coverage_results": results, "status": "done", "errors": errors}
