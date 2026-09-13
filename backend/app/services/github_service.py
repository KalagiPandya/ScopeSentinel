"""
GitHub Repository Intelligence service (Agent 3 support).

Connects to a GitHub repository and builds a lightweight "knowledge graph"
of the codebase. Includes realistic fallback data for demo repositories.
"""
from typing import List, Dict, Optional


def _get_repo(repo_url: str, token: Optional[str] = None):
    from github import Github

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
        if "frontend" in lower or "client" in lower or "src/components" in lower:
            return "frontend"
        if "backend" in lower or "server" in lower or "api" in lower:
            return "backend"
        return "frontend"
    return "other"


def scan_repository(repo_url: str, token: Optional[str] = None, max_files: int = 300) -> Dict:
    try:
        repo = _get_repo(repo_url, token)
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

        readme_excerpt = ""
        try:
            readme = repo.get_readme()
            readme_excerpt = readme.decoded_content.decode("utf-8", errors="ignore")[:2000]
        except Exception:
            pass

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
    except Exception as e:
        print(f"[GitHub Notice] Using demo repository intelligence: {e}")
        demo_files = [
            {"path": "backend/app/main.py", "type": "backend", "size": 2500},
            {"path": "backend/app/api/auth.py", "type": "backend", "size": 1800},
            {"path": "backend/app/api/attendance.py", "type": "backend", "size": 3200},
            {"path": "backend/app/models/user.py", "type": "database", "size": 1200},
            {"path": "backend/app/models/student.py", "type": "database", "size": 1500},
            {"path": "frontend/src/pages/Dashboard.jsx", "type": "frontend", "size": 4200},
            {"path": "frontend/src/pages/Attendance.jsx", "type": "frontend", "size": 3800},
            {"path": "frontend/src/pages/Login.jsx", "type": "frontend", "size": 2100},
            {"path": "backend/tests/test_auth.py", "type": "test", "size": 1600},
            {"path": "backend/tests/test_attendance.py", "type": "test", "size": 1900},
            {"path": "Dockerfile", "type": "config", "size": 400},
            {"path": "docker-compose.yml", "type": "config", "size": 800},
        ]
        return {
            "repo_name": repo_url.replace("https://github.com/", ""),
            "description": "College Management System full-stack engineering platform",
            "default_branch": "main",
            "readme_excerpt": "# College Management System\nFull-stack academic platform for attendance tracking, student portals, and grade management.",
            "files": demo_files,
            "file_counts": {"frontend": 3, "backend": 3, "database": 2, "test": 2, "config": 2, "other": 0},
            "total_files": len(demo_files),
            "recent_commits": [
                {"sha": "a1b2c3d", "message": "feat: add OTP authentication endpoint", "author": "Priya Patel"},
                {"sha": "e4f5g6h", "message": "fix: attendance calculation threshold", "author": "Amit Singh"},
            ],
        }


def get_pr_changed_files(repo_url: str, pr_number: int, token: Optional[str] = None) -> List[str]:
    try:
        repo = _get_repo(repo_url, token)
        pr = repo.get_pull(pr_number)
        return [f.filename for f in pr.get_files()]
    except Exception:
        return [
            "backend/app/api/auth.py",
            "backend/app/api/attendance.py",
            "frontend/src/pages/Attendance.jsx",
            "backend/app/services/otp_service.py"
        ]


def get_pr_details(repo_url: str, pr_number: int, token: Optional[str] = None) -> Dict:
    try:
        repo = _get_repo(repo_url, token)
        pr = repo.get_pull(pr_number)
        return {
            "title": pr.title,
            "body": pr.body or "",
            "changed_files": [f.filename for f in pr.get_files()],
            "author": pr.user.login if pr.user else "unknown",
            "state": pr.state,
        }
    except Exception as e:
        print(f"[GitHub Notice] Serving sample PR #{pr_number} details: {e}")
        return {
            "title": f"feat(auth): add student OTP login and attendance summary #{pr_number}",
            "body": "This PR implements 6-digit SMS OTP verification during student login and adds attendance rate calculations for the student portal.",
            "changed_files": [
                "backend/app/api/auth.py",
                "backend/app/api/attendance.py",
                "frontend/src/pages/Attendance.jsx",
                "backend/app/services/otp_service.py"
            ],
            "author": "priya-dev",
            "state": "open",
        }


def post_pr_comment(repo_url: str, pr_number: int, comment_markdown: str, token: Optional[str] = None) -> bool:
    try:
        repo = _get_repo(repo_url, token)
        pr = repo.get_pull(pr_number)
        pr.create_issue_comment(comment_markdown)
        return True
    except Exception:
        return False


def get_open_issues(repo_url: str, token: Optional[str] = None, max_issues: int = 20) -> List[Dict]:
    try:
        repo = _get_repo(repo_url, token)
        issues = []
        for issue in repo.get_issues(state="open")[:max_issues]:
            if issue.pull_request:
                continue
            issues.append({
                "number": issue.number,
                "title": issue.title,
                "body": (issue.body or "")[:500],
                "labels": [l.name for l in issue.labels],
            })
        return issues
    except Exception:
        return [
            {"number": 101, "title": "OTP verification timing out on slow networks", "body": "Need to extend timeout to 60s", "labels": ["bug", "auth"]},
            {"number": 102, "title": "Add attendance percentage progress bar", "body": "UI enhancement for student portal", "labels": ["enhancement", "frontend"]},
        ]
