import { useState } from "react";
import { Upload, Zap } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import RiskBadge from "../components/RiskBadge";
import { useProject } from "../context/ProjectContext";
import { agent } from "../api/client";

const SOURCES = ["meeting", "email", "document", "jira", "github_issue"];

const SAMPLE_TEXT = `Quick update from today's client call.

The client wants to add OTP verification to the student login flow,
on top of the existing email and password. This is a new security
requirement from their compliance team.

Also, faculty should now be able to see a full history of all the
leave applications they have processed — both approved and rejected —
not just the pending ones. This was requested by the HOD.

The 2-second API response time requirement is still in place.`;

export default function UploadCenter() {
  const { currentProject } = useProject();
  const [text, setText] = useState(SAMPLE_TEXT);
  const [source, setSource] = useState("meeting");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleRun = async () => {
    if (!text.trim()) { setError("Enter some text first."); return; }
    if (!currentProject) { setError("Select a project first."); return; }
    setError(""); setRunning(true); setResult(null);
    try {
      const res = await agent.run({ project_id: currentProject.id, text, source });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Pipeline failed. Check backend logs and OPENAI_API_KEY.");
    } finally { setRunning(false); }
  };

  return (
    <Layout title="Upload Center">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="space-y-4">
          <Card title="Input Text" eyebrow="Agents 1-2-5-6-8">
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-mono text-ink-500 mb-1">SOURCE TYPE</label>
                <select value={source} onChange={e => setSource(e.target.value)}
                  className="w-full bg-base-600 border border-base-500 rounded px-3 py-2 text-sm text-ink-100 focus:border-signal/50 outline-none">
                  {SOURCES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1).replace("_", " ")}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-mono text-ink-500 mb-1">TEXT (meeting transcript, email, document)</label>
                <textarea value={text} onChange={e => setText(e.target.value)} rows={10}
                  className="w-full bg-base-600 border border-base-500 rounded px-3 py-2 text-sm text-ink-100 focus:border-signal/50 outline-none resize-none font-mono leading-relaxed"
                  placeholder="Paste meeting transcript, email, or requirement document here..."/>
              </div>
              {error && <p className="text-xs text-risk-critical">{error}</p>}
              <button onClick={handleRun} disabled={running || !currentProject}
                className="w-full flex items-center justify-center gap-2 bg-signal text-base-900 font-semibold text-sm py-2.5 rounded hover:bg-signal/90 transition-colors disabled:opacity-50">
                <Zap size={14}/>{running ? "Running pipeline (Agents 1→2→5→6→8)..." : "Run Agent Pipeline"}
              </button>
              <p className="text-xs text-ink-500">
                The sample text above demonstrates the core ScopeSentinel scenario —
                OTP added to login (modification) and a new leave history requirement (new addition).
              </p>
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          {result && (
            <>
              <Card title="Pipeline Complete" eyebrow={result.summary}>
                <div className="grid grid-cols-2 gap-3 text-center">
                  <div className="bg-base-600 rounded p-3">
                    <div className="text-2xl font-mono font-bold text-ink-100">{result.total_extracted}</div>
                    <div className="text-xs font-mono text-ink-500 mt-1">EXTRACTED</div>
                  </div>
                  <div className="bg-base-600 rounded p-3">
                    <div className="text-2xl font-mono font-bold text-ink-100">{result.total_changes_detected}</div>
                    <div className="text-xs font-mono text-ink-500 mt-1">CHANGES</div>
                  </div>
                </div>
                {result.errors?.length > 0 && (
                  <div className="mt-3 text-xs text-risk-medium">
                    {result.errors.map((e, i) => <div key={i}>{e}</div>)}
                  </div>
                )}
              </Card>

              {result.modifications_saved?.length > 0 && (
                <Card title="Modifications Detected" eyebrow={`${result.modifications_saved.length} change(s)`}>
                  <div className="space-y-3">
                    {result.modifications_saved.map((m, i) => (
                      <div key={i} className="border-b border-base-500 last:border-0 pb-3 last:pb-0">
                        <p className="text-sm text-ink-100 mb-1">{m.text}</p>
                        <div className="flex items-center gap-3">
                          {m.risk && <RiskBadge level={m.risk.risk_level} score={m.risk.risk_score}/>}
                          <span className="text-xs font-mono text-ink-500">similarity: {(m.similarity_score * 100).toFixed(0)}%</span>
                        </div>
                        {m.risk?.justification && (
                          <p className="text-xs text-ink-500 mt-1">{m.risk.justification}</p>
                        )}
                        {m.impact?.total_affected > 0 && (
                          <p className="text-xs font-mono text-ink-500 mt-1">
                            {m.impact.total_affected} module(s) affected
                          </p>
                        )}
                        {m.notification && (
                          <p className="text-xs font-mono mt-1" style={{ color: m.risk?.risk_level === "critical" ? "#F87171" : m.risk?.risk_level === "high" ? "#FB923C" : "#9BAAB9" }}>
                            Notified via: {m.notification.sent_channels.join(", ")}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {result.new_requirements_saved?.length > 0 && (
                <Card title="New Requirements Added" eyebrow={`${result.new_requirements_saved.length} new`}>
                  <div className="space-y-3">
                    {result.new_requirements_saved.map((n, i) => (
                      <div key={i} className="border-b border-base-500 last:border-0 pb-3 last:pb-0">
                        <p className="text-sm text-ink-100 mb-1">{n.text}</p>
                        {n.risk && <RiskBadge level={n.risk.risk_level} score={n.risk.risk_score}/>}
                        {n.notification && (
                          <p className="text-xs font-mono text-ink-500 mt-1">
                            Notified via: {n.notification.sent_channels.join(", ")}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {result.total_changes_detected === 0 && (
                <Card>
                  <div className="flex items-center gap-2 py-4 text-sm text-ink-300">
                    <span className="pulse-dot bg-risk-low"/>
                    All requirements already exist in the baseline. No changes detected.
                  </div>
                </Card>
              )}
            </>
          )}

          {!result && !running && (
            <Card>
              <div className="flex flex-col items-center py-10 text-center">
                <Upload size={32} className="text-ink-500 mb-3"/>
                <p className="text-sm text-ink-300 mb-1">Results appear here after the pipeline runs.</p>
                <p className="text-xs text-ink-500 max-w-xs">The sample text in the editor is pre-filled with the core ScopeSentinel demo scenario from the SRS.</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </Layout>
  );
}
