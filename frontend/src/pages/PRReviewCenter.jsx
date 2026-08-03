import { useState } from "react";
import { GitPullRequest, Play } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import { useProject } from "../context/ProjectContext";
import { prReview } from "../api/client";

const REC_STYLE = {
  approve:         { label: "APPROVE",          cls: "text-risk-low  bg-risk-low/10  border-risk-low/30" },
  request_changes: { label: "REQUEST CHANGES",  cls: "text-risk-high bg-risk-high/10 border-risk-high/30" },
  comment_only:    { label: "COMMENT ONLY",      cls: "text-ink-300   bg-base-600     border-base-500" },
};

export default function PRReviewCenter() {
  const { currentProject } = useProject();
  const [prNumber, setPrNumber] = useState("");
  const [postComment, setPostComment] = useState(false);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);

  const handleRun = async () => {
    const num = parseInt(prNumber, 10);
    if (!num || num < 1) { setError("Enter a valid PR number."); return; }
    if (!currentProject?.github_repo_url) {
      setError("Project has no GitHub repo URL. Update via PUT /projects/{id} first.");
      return;
    }
    setError(""); setRunning(true); setResult(null);
    try {
      const res = await prReview.run({ project_id: currentProject.id, pr_number: num, post_comment: postComment });
      setResult(res.data);
      setHistory(h => [res.data, ...h].slice(0, 10));
    } catch (e) {
      setError(e.response?.data?.detail || "PR review failed. Check GitHub repo URL and OpenAI key.");
    } finally { setRunning(false); }
  };

  const rec = result?.review?.recommendation ? REC_STYLE[result.review.recommendation] || REC_STYLE.comment_only : null;

  return (
    <Layout title="PR Review Center">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card title="Run PR Review" eyebrow="Agent 7" className="lg:col-span-1">
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-mono text-ink-500 mb-1">PR NUMBER</label>
              <input value={prNumber} onChange={e => setPrNumber(e.target.value)}
                type="number" min="1" placeholder="42"
                className="w-full bg-base-600 border border-base-500 rounded px-3 py-2 text-sm text-ink-100 focus:border-signal/50 outline-none"/>
            </div>
            <label className="flex items-center gap-2 text-sm text-ink-300 cursor-pointer">
              <input type="checkbox" checked={postComment} onChange={e => setPostComment(e.target.checked)}
                className="rounded border-base-500 bg-base-600"/>
              Post comment on GitHub PR
            </label>
            {error && <p className="text-xs text-risk-critical">{error}</p>}
            <button onClick={handleRun} disabled={running || !currentProject}
              className="w-full flex items-center justify-center gap-2 bg-signal text-base-900 font-semibold text-sm py-2 rounded hover:bg-signal/90 transition-colors disabled:opacity-50">
              <Play size={14}/>{running ? "Reviewing..." : "Run AI Review"}
            </button>
            {currentProject?.github_repo_url && (
              <p className="text-xs text-ink-500 break-all">Repo: {currentProject.github_repo_url}</p>
            )}
          </div>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          {result && (
            <Card title={`PR #${result.pr_number} — ${result.pr_title}`} eyebrow="AI Review Result">
              <div className="flex items-center gap-4 mb-4">
                <div className="text-center">
                  <div className="text-3xl font-mono font-bold text-ink-100">{result.review.compliance_score}</div>
                  <div className="text-xs font-mono text-ink-500">COMPLIANCE /100</div>
                </div>
                {rec && (
                  <span className={`text-xs font-mono px-3 py-1 rounded border ${rec.cls}`}>{rec.label}</span>
                )}
              </div>

              {result.review.matched_requirements?.length > 0 && (
                <div className="mb-3">
                  <div className="text-xs font-mono text-ink-500 mb-1">MATCHED REQUIREMENTS</div>
                  {result.review.matched_requirements.map((r, i) => (
                    <div key={i} className="text-xs text-ink-300 flex items-start gap-1 mb-1">
                      <span className="text-signal">→</span>{r}
                    </div>
                  ))}
                </div>
              )}

              {result.review.missing_items?.length > 0 && (
                <div className="mb-3">
                  <div className="text-xs font-mono text-risk-high mb-1">MISSING / TO REVIEW</div>
                  {result.review.missing_items.map((m, i) => (
                    <div key={i} className="text-xs text-ink-300 flex items-start gap-1 mb-1">
                      <span className="text-risk-high">⚠</span>{m}
                    </div>
                  ))}
                </div>
              )}

              <div className="text-sm text-ink-300 mb-4">{result.review.summary}</div>

              <details className="text-xs">
                <summary className="text-ink-500 font-mono cursor-pointer hover:text-ink-300 transition-colors">
                  VIEW GITHUB COMMENT MARKDOWN
                </summary>
                <pre className="mt-2 p-3 bg-base-600 rounded text-ink-300 whitespace-pre-wrap overflow-x-auto text-xs leading-relaxed">
                  {result.review.comment_markdown}
                </pre>
              </details>

              {result.comment_posted && (
                <div className="mt-3 text-xs text-risk-low flex items-center gap-1">
                  ✓ Comment posted on GitHub PR
                </div>
              )}
            </Card>
          )}

          {history.length > 0 && (
            <Card title="Review History" eyebrow="This Session">
              <div className="space-y-2">
                {history.map((h, i) => {
                  const cfg = REC_STYLE[h.review?.recommendation] || REC_STYLE.comment_only;
                  return (
                    <div key={i} className="flex items-center justify-between text-sm p-2 rounded bg-base-600">
                      <div>
                        <span className="font-mono text-signal">PR #{h.pr_number}</span>
                        <span className="text-ink-300 ml-2 truncate">{h.pr_title}</span>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="font-mono text-ink-100">{h.review?.compliance_score}/100</span>
                        <span className={`text-xs px-2 py-0.5 rounded border font-mono ${cfg.cls}`}>{cfg.label}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {!result && !running && (
            <Card>
              <div className="flex flex-col items-center py-10 text-center">
                <GitPullRequest size={32} className="text-ink-500 mb-3"/>
                <p className="text-sm text-ink-300 mb-1">Enter a PR number and click Run AI Review.</p>
                <p className="text-xs text-ink-500 max-w-sm">Agent 7 will fetch the PR from GitHub, match it to your project requirements, and score its compliance.</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </Layout>
  );
}
