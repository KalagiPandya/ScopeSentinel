import { useEffect, useState } from "react";
import { Bell } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import RiskBadge from "../components/RiskBadge";
import { useProject } from "../context/ProjectContext";
import client from "../api/client";

export default function Notifications() {
  const { currentProject } = useProject();
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!currentProject) return;
    setLoading(true);
    client.get(`/changes/project/${currentProject.id}`)
      .then(res => setAlerts(res.data.filter(c => c.risk_level)))
      .finally(() => setLoading(false));
  }, [currentProject]);

  const CHANNEL_STYLE = { dashboard: "bg-signal/10 text-signal", email: "bg-risk-medium/10 text-risk-medium", slack: "bg-risk-low/10 text-risk-low", email_stub: "bg-base-600 text-ink-500", slack_stub: "bg-base-600 text-ink-500" };

  return (
    <Layout title="Notifications">
      <div className="mb-4 text-sm text-ink-300">
        Showing alerts from detected requirement changes. Configure real Slack/email delivery
        by adding <code className="font-mono text-signal text-xs">SLACK_WEBHOOK_URL</code> and
        SMTP settings to your <code className="font-mono text-signal text-xs">.env</code> file.
      </div>
      {loading ? (
        <Card><div className="text-sm text-ink-500 py-4 text-center">Loading...</div></Card>
      ) : alerts.length === 0 ? (
        <Card>
          <div className="flex flex-col items-center py-10 text-center">
            <Bell size={32} className="text-ink-500 mb-3"/>
            <p className="text-sm text-ink-300">No alerts yet.</p>
            <p className="text-xs text-ink-500 mt-1">Run the agent pipeline to generate risk-scored changes.</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {alerts.map(a => (
            <Card key={a.id}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <RiskBadge level={a.risk_level} score={a.risk_score}/>
                    <span className="text-xs font-mono text-ink-500">{a.change_type?.replace("_", " ")}</span>
                  </div>
                  <p className="text-sm text-ink-300">{a.risk_justification}</p>
                  {a.impact_map?.total_affected > 0 && (
                    <p className="text-xs font-mono text-ink-500 mt-1">{a.impact_map.total_affected} module(s) affected</p>
                  )}
                </div>
                <div className="flex flex-col gap-1 items-end shrink-0">
                  {(a.risk_level === "critical" ? ["dashboard", "email", "slack"] :
                    a.risk_level === "high" ? ["dashboard", "email"] : ["dashboard"]).map(ch => (
                    <span key={ch} className={`text-[10px] font-mono px-2 py-0.5 rounded ${CHANNEL_STYLE[ch] || CHANNEL_STYLE.dashboard}`}>{ch}</span>
                  ))}
                </div>
              </div>
              <div className="text-[11px] font-mono text-ink-500 mt-2">
                {new Date(a.detected_at).toLocaleString()}
              </div>
            </Card>
          ))}
        </div>
      )}
    </Layout>
  );
}
