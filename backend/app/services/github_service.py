"""
GitHub Repository Intelligence service (Agent 3 support).

Connects to a GitHub repository and builds a lightweight "knowledge graph"
of the codebase: file paths, classified by type (frontend/backend/database/
test/config/other), plus README content and recent commit messages.

This is intentionally LIGHTWEIGHT — we do NOT clone the repo. We use the
GitHub REST API (via PyGithub) to list the file tree and fetch small files
(like README) directly. This keeps it fast and works for public repos
without any token, or private repos with a personal access token.
"""
from typing import List, Dict, Optional


def _get_repo(repo_url: str, token: Optional[str] = None):
    from github import Github

    # Accept full URLs like https://github.com/owner/name or owner/name
    repo_path = repo_url.replace("https://github.com/", "").replace("http://github.com/", "")
    repo_path = repo_path.rstrip("/").rstrip(".git")

    gh = Github(token) if token else Github()
    return gh.get_repo(repo_path)


# ── File classification ─────────────────────────────────────────────────

FRONTEND_EXT = {".jsx", ".tsx", ".vue", ".html", ".css", ".scss"}
BACKEND_EXT = {".py", ".java", ".go", ".rb", ".php", ".cs"}
JS_EXT = {".js", ".ts"}
TEST_HINTS = {"test", "spec", "__tests__"}
DB_HINTS = {"migration", "schema", "model", "models", "alembic"}
CONFIG_FILES = {
    "dockerfile", "docker-compose.yml", "package.json", "requirements.txt",
    ".env.example", "tsconfig.json", "vite.config.js", "webpack.config.js",
}


def classify_file(path: str) -> str:
    """
    Classify a file path into: frontend | backend | database | test | config | other
    Based on extension and path keywords — heuristic, not perfect, but fast.
    """
    lower = path.lower()
    filename = lower.split("/")[-1]
    ext = "." + filename.split(".")[-1] if "." in filename else ""

    if any(h in lower for h in TEST_HINTS):
        return "test"
    if filename in CONFIG_FILES or filename.startswith("docker"):
        return "config"
    if any(h in lower for h in DB_HINTS):
        return "database"
    if ext in FRONTEND_EXT:
        return "frontend"
    if ext in BACKEND_EXT:
        return "backend"
    if ext in JS_EXT:
        # ambiguous — guess based on path
        if "frontend" in lower or "client" in lower or "src/components" in lower:
            return "frontend"
        if "backend" in lower or "server" in lower or "api" in lower:
            return "backend"
        return "frontend"  # default JS/TS to frontend
    return "other"


def scan_repository(repo_url: str, token: Optional[str] = None, max_files: int = 300) -> Dict:
    """
    Scan a GitHub repository and return a knowledge-graph summary.

    Returns:
    {
      "repo_name": "owner/name",
      "description": "...",
      "readme_excerpt": "...",
      "files": [{"path": "...", "type": "frontend|backend|...", "size": N}, ...],
      "file_counts": {"frontend": N, "backend": N, "database": N, "test": N, "config": N, "other": N},
      "recent_commits": [{"sha": "...", "message": "...", "author": "..."}],
    }
    """
    repo = _get_repo(repo_url, token)

    # ── File tree ────────────────────────────────────────────────────────
    files = []
    try:
        contents = repo.get_git_tree(repo.default_branch, recursive=True).tree
    except Exception:
        contents = []

    for item in contents:
        if item.type != "blob":
            continue
        path = item.path
        files.append({
            "path": path,
            "type": classify_file(path),
            "size": item.size or 0,
        })
        if len(files) >= max_files:
            break

    file_counts = {"frontend": 0, "backend": 0, "database": 0, "test": 0, "config": 0, "other": 0}
    for f in files:
        file_counts[f["type"]] += 1

    # ── README ───────────────────────────────────────────────────────────
    readme_excerpt = ""
    try:
        readme = repo.get_readme()
        content = readme.decoded_content.decode("utf-8", errors="ignore")
        readme_excerpt = content[:2000]
    except Exception:
        pass

    # ── Recent commits ───────────────────────────────────────────────────
    recent_commits = []
    try:
        for commit in repo.get_commits()[:10]:
            recent_commits.append({
                "sha": commit.sha[:7],
                "message": commit.commit.message.split("\n")[0][:120],
                "author": commit.commit.author.name if commit.commit.author else "unknown",
            })
    except Exception:
        pass

    return {
        "repo_name": repo.full_name,
        "description": repo.description or "",
        "default_branch": repo.default_branch,
        "readme_excerpt": readme_excerpt,
        "files": files,
        "file_counts": file_counts,
        "total_files": len(files),
        "recent_commits": recent_commits,
    }


def get_pr_changed_files(repo_url: str, pr_number: int, token: Optional[str] = None) -> List[str]:
    """Return list of file paths changed in a PR."""
    repo = _get_repo(repo_url, token)
    pr = repo.get_pull(pr_number)
    return [f.filename for f in pr.get_files()]


def get_pr_details(repo_url: str, pr_number: int, token: Optional[str] = None) -> Dict:
    """Return title, body, and changed files for a PR."""
    repo = _get_repo(repo_url, token)
    pr = repo.get_pull(pr_number)
    return {
        "title": pr.title,
        "body": pr.body or "",
        "changed_files": [f.filename for f in pr.get_files()],
        "author": pr.user.login if pr.user else "unknown",
        "state": pr.state,
    }


def post_pr_comment(repo_url: str, pr_number: int, comment_markdown: str, token: Optional[str] = None) -> bool:
    """
    Post a review comment on a GitHub PR.
    Requires a token with `repo` write access (for private repos) or
    public_repo scope (for public repos).
    Returns True if posted successfully.
    """
    repo = _get_repo(repo_url, token)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(comment_markdown)
    return True


def get_open_issues(repo_url: str, token: Optional[str] = None, max_issues: int = 20) -> List[Dict]:
    """Fetch open issues — useful for linking issues to requirements."""
    repo = _get_repo(repo_url, token)
    issues = []
    for issue in repo.get_issues(state="open")[:max_issues]:
        if issue.pull_request:  # skip PRs returned by get_issues
            continue
        issues.append({
            "number": issue.number,
            "title": issue.title,
            "body": (issue.body or "")[:500],
            "labels": [l.name for l in issue.labels],
        })
    return issues
