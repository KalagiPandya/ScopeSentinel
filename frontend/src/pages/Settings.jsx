import { useState } from "react";
import { Settings as SettingsIcon, CheckCircle } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import { useProject } from "../context/ProjectContext";
import client from "../api/client";

export default function Settings() {
  const { currentProject, setProjectList } = useProject();
  const [repoUrl, setRepoUrl] = useState(currentProject?.github_repo_url || "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    if (!currentProject) return;
    setSaving(true); setSaved(false);
    try {
      const res = await client.put(`/projects/${currentProject.id}`, { github_repo_url: repoUrl });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      alert("Save failed: " + (e.response?.data?.detail || e.message));
    } finally { setSaving(false); }
  };

  return (
    <Layout title="Settings">
      <div className="max-w-xl space-y-4">
        <Card title="Project Settings" eyebrow={currentProject?.name || "No project selected"}>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-mono text-ink-500 mb-1">GITHUB REPO URL</label>
              <input value={repoUrl} onChange={e => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                className="w-full bg-base-600 border border-base-500 rounded px-3 py-2 text-sm text-ink-100 focus:border-signal/50 outline-none"/>
              <p className="text-xs text-ink-500 mt-1">Used by Agent 3 (GitHub scan), Agent 7 (PR review), and the GitHub webhook.</p>
            </div>
            <button onClick={handleSave} disabled={saving || !currentProject}
              className="flex items-center gap-2 bg-signal text-base-900 font-semibold text-sm px-4 py-2 rounded hover:bg-signal/90 transition-colors disabled:opacity-50">
              {saved ? <><CheckCircle size={14}/> Saved!</> : saving ? "Saving..." : "Save Settings"}
            </button>
          </div>
        </Card>

        <Card title="Backend Configuration" eyebrow="Read-only Reference">
          <div className="space-y-2 font-mono text-xs">
            {[
              ["API URL", "http://localhost:8000"],
              ["Docs", "http://localhost:8000/docs"],
              ["Neo4j Browser", "http://localhost:7474"],
              ["Qdrant Dashboard", "http://localhost:6333/dashboard"],
              ["Agents", "8 (running in 3 LangGraph pipelines)"],
              ["Endpoints", "33 REST endpoints"],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between py-1.5 border-b border-base-500 last:border-0">
                <span className="text-ink-500">{k}</span>
                <span className="text-ink-300">{v}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Agent Configuration" eyebrow="Notification Channels">
          <p className="text-sm text-ink-300 mb-3">Configure real delivery in your backend <code className="font-mono text-signal text-xs">.env</code> file:</p>
          <div className="space-y-1 font-mono text-xs text-ink-500">
            {["SLACK_WEBHOOK_URL=https://hooks.slack.com/...", "SMTP_HOST=smtp.gmail.com", "SMTP_PORT=587", "SMTP_USER=you@gmail.com", "SMTP_PASSWORD=app-password", "SMTP_FROM=scopesentinel@yourapp.com"].map(line => (
              <div key={line} className="bg-base-600 px-3 py-1 rounded text-ink-300">{line}</div>
            ))}
          </div>
          <p className="text-xs text-ink-500 mt-3">Without these, Agent 8 gracefully stubs Slack/email (prints to console) and always logs to dashboard.</p>
        </Card>
      </div>
    </Layout>
  );
}
