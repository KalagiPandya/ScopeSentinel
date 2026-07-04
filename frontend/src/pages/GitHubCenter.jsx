import { useEffect, useState } from "react";
import { Github, GitCommit, FolderOpen, RefreshCw } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import { useProject } from "../context/ProjectContext";
import { github } from "../api/client";

export default function GitHubCenter() {
  const { currentProject } = useProject();
  const [repoUrl, setRepoUrl] = useState("");
  const [token, setToken] = useState("");
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (currentProject?.github_repo_url) setRepoUrl(currentProject.github_repo_url);
  }, [currentProject]);

  const handleScan = async () => {
    if (!repoUrl.trim()) { setError("Enter a GitHub repo URL first."); return; }
    setError(""); setScanning(true); setResult(null);
    try {
      const res = await github.scanCoverage({
        project_id: currentProject.id,
        repo_url: repoUrl,
        github_token: token || null,
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Scan failed. Check repo URL and OpenAI key.");
    } finally { setScanning(false); }
  };

  const fc = result?.repo_summary?.file_counts || {};
  const fileBars = [
    { label: "Frontend", key: "frontend", color: "#3B9EFF" },
    { label: "Backend",  key: "backend",  color: "#A78BFA" },
    { label: "Database", key: "database", color: "#4ADE80" },
    { label: "Tests",    key: "test",     color: "#FBBF24" },
    { label: "Config",   key: "config",   color: "#FB923C" },
  ];

  return (
    <Layout title="GitHub Center">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card title="Repository Scanner" eyebrow="Agent 3" className="lg:col-span-1">
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-mono text-ink-500 mb-1">REPO URL</label>
              <input value={repoUrl} onChange={e => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                className="w-full bg-base-600 border border-base-500 rounded px-3 py-2 text-sm text-ink-100 focus:border-signal/50 outline-none"/>
            </div>
            <div>
              <label className="block text-xs font-mono text-ink-500 mb-1">GITHUB TOKEN (private repos)</label>
              <input value={token} onChange={e => setToken(e.target.value)} type="password"
                placeholder="ghp_optional_token"
                className="w-full bg-base-600 border border-base-500 rounded px-3 py-2 text-sm text-ink-100 focus:border-signal/50 outline-none"/>
            </div>
            {error && <p className="text-xs text-risk-critical">{error}</p>}
            <button onClick={handleScan} disabled={scanning || !currentProject}
              className="w-full flex items-center justify-center gap-2 bg-signal text-base-900 font-semibold text-sm py-2 rounded hover:bg-signal/90 transition-colors disabled:opacity-50">
              <RefreshCw size={14} className={scanning ? "animate-spin" : ""} />
              {scanning ? "Scanning repo..." : "Scan Repository"}
            </button>
            <p className="text-xs text-ink-500">
              Scans the repo file tree and calculates a Coverage Score for every
              requirement. Requires OPENAI_API_KEY in backend .env.
            </p>
          </div>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          {result?.repo_summary && (
            <Card title={result.repo_summary.repo_name} eyebrow="Repository Overview">
              <p className="text-sm text-ink-300 mb-4">{result.repo_summary.description || "No description"}</p>
              <div className="space-y-2 mb-4">
                {fileBars.map(({ label, key, color }) => {
                  const count = fc[key] || 0;
                  const total = result.repo_summary.total_files || 1;
                  const pct = Math.round((count / total) * 100);
                  return (
                    <div key={key}>
                      <div className="flex justify-between text-xs font-mono mb-1">
                        <span className="text-ink-300">{label}</span>
                        <span style={{ color }}>{count} files</span>
                      </div>
                      <div className="h-1.5 bg-base-500 rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }}/>
                      </div>
                    </div>
                  );
                })}
              </div>
              {result.repo_summary.recent_commits?.length > 0 && (
                <div>
                  <div className="text-xs font-mono text-ink-500 mb-2">RECENT COMMITS</div>
                  <div className="space-y-1">
                    {result.repo_summary.recent_commits.slice(0, 5).map((c, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs">
                        <GitCommit size={12} className="text-ink-500 shrink-0"/>
                        <span className="font-mono text-signal">{c.sha}</span>
                        <span className="text-ink-300 truncate">{c.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          )}

          {result && (
            <Card title="Coverage Summary" eyebrow="From This Scan">
              <div className="flex items-center gap-8 mb-4">
                <div className="text-center">
                  <div className="text-3xl font-mono font-bold text-ink-100">{result.overall_coverage_percent}%</div>
                  <div className="text-xs font-mono text-ink-500 mt-1">OVERALL COVERAGE</div>
                </div>
                <div className="text-sm space-y-1">
                  <div><span className="text-risk-low">●</span> <span className="text-ink-300">Fully implemented:</span> <span className="font-mono text-ink-100">{result.coverage_results?.filter(r => r.status === "fully_implemented").length || 0}</span></div>
                  <div><span className="text-risk-medium">●</span> <span className="text-ink-300">Partial:</span> <span className="font-mono text-ink-100">{result.coverage_results?.filter(r => r.status === "partially_implemented").length || 0}</span></div>
                  <div><span className="text-risk-critical">●</span> <span className="text-ink-300">Not implemented:</span> <span className="font-mono text-ink-100">{result.coverage_results?.filter(r => r.status === "not_implemented").length || 0}</span></div>
                </div>
              </div>
              <p className="text-xs text-ink-500">View full requirement breakdown in Coverage Center.</p>
            </Card>
          )}

          {!result && !scanning && (
            <Card>
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <Github size={32} className="text-ink-500 mb-3"/>
                <p className="text-sm text-ink-300 mb-1">Enter a GitHub repository URL and click Scan.</p>
                <p className="text-xs text-ink-500">Agent 3 will classify every file. Agent 4 will score each requirement's coverage.</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </Layout>
  );
}
