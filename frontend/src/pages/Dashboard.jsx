import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { ListChecks, GitBranch, Target, AlertTriangle } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import RiskBadge, { RISK_COLORS } from "../components/RiskBadge";
import { useProject } from "../context/ProjectContext";
import { analytics, changes as changesApi } from "../api/client";

function StatCard({ icon: Icon, label, value, accent }) {
  return (
    <div className="bg-base-700 border border-base-500 rounded-lg shadow-panel p-5 flex items-center gap-4">
      <div
        className="w-10 h-10 rounded-md flex items-center justify-center shrink-0"
        style={{ backgroundColor: `${accent}1A`, color: accent }}
      >
        <Icon size={20} />
      </div>
      <div>
        <div className="text-2xl font-mono font-bold text-ink-100">{value}</div>
        <div className="text-xs text-ink-500 uppercase tracking-wider font-mono">{label}</div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { currentProject } = useProject();
  const [summary, setSummary] = useState(null);
  const [recentChanges, setRecentChanges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!currentProject) return;
    setLoading(true);
    setError("");

    Promise.all([
      analytics.summary(currentProject.id),
      changesApi.listByProject(currentProject.id),
    ])
      .then(([summaryRes, changesRes]) => {
        setSummary(summaryRes.data);
        setRecentChanges(changesRes.data.slice(0, 6));
      })
      .catch(() => setError("Could not load dashboard data. Is the backend running?"))
      .finally(() => setLoading(false));
  }, [currentProject]);

  if (!currentProject) {
    return (
      <Layout title="Dashboard">
        <Card>
          <p className="text-ink-300 text-sm">
            No project selected. Create a project via the API or select one from the
            project switcher above.
          </p>
        </Card>
      </Layout>
    );
  }

  const riskDist = summary?.risk_distribution || {};
  const pieData = ["low", "medium", "high", "critical"]
    .map((level) => ({ name: level, value: riskDist[level] || 0 }))
    .filter((d) => d.value > 0);

  const coverage = summary?.coverage || {};

  return (
    <Layout title="Dashboard">
      {error && (
        <div className="mb-4 text-sm text-risk-critical bg-risk-critical/10 border border-risk-critical/20 rounded-md px-4 py-2">
          {error}
        </div>
      )}

      {/* Hero strip */}
      <div className="mb-6">
        <div className="text-xs font-mono uppercase tracking-wider text-ink-500 mb-1">
          {currentProject.name}
        </div>
        <h2 className="text-2xl font-semibold text-ink-100">
          {loading ? "Scanning project signals..." : "Project Health Overview"}
        </h2>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          icon={ListChecks}
          label="Total Requirements"
          value={summary?.total_requirements ?? "—"}
          accent="#3B9EFF"
        />
        <StatCard
          icon={GitBranch}
          label="Total Changes Detected"
          value={summary?.total_changes ?? "—"}
          accent="#A78BFA"
        />
        <StatCard
          icon={Target}
          label="Avg. Coverage"
          value={coverage.average_percent != null ? `${coverage.average_percent}%` : "—"}
          accent="#4ADE80"
        />
        <StatCard
          icon={AlertTriangle}
          label="High + Critical Changes"
          value={(riskDist.high || 0) + (riskDist.critical || 0)}
          accent="#F87171"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Risk distribution */}
        <Card title="Risk Distribution" eyebrow="Requirement Changes" className="lg:col-span-1">
          {pieData.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-sm text-ink-500">
              No changes detected yet
            </div>
          ) : (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={45}
                    outerRadius={70}
                    paddingAngle={3}
                  >
                    {pieData.map((entry) => (
                      <Cell key={entry.name} fill={RISK_COLORS[entry.name]} stroke="none" />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: "#131A24", border: "1px solid #26303F", borderRadius: 8, fontSize: 12 }}
                    labelStyle={{ color: "#E6EDF3" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
          <div className="flex flex-wrap gap-3 mt-3">
            {["low", "medium", "high", "critical"].map((level) => (
              <div key={level} className="flex items-center gap-1.5 text-xs">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: RISK_COLORS[level] }} />
                <span className="text-ink-500 capitalize">{level}</span>
                <span className="text-ink-100 font-mono">{riskDist[level] || 0}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Coverage breakdown */}
        <Card title="Requirement Coverage" eyebrow="From GitHub Analysis" className="lg:col-span-1">
          <div className="space-y-3">
            <CoverageRow label="Fully Implemented" value={coverage.fully_implemented || 0} color="#4ADE80" />
            <CoverageRow label="Partially Implemented" value={coverage.partially_implemented || 0} color="#FBBF24" />
            <CoverageRow label="Not Implemented" value={coverage.not_implemented || 0} color="#F87171" />
          </div>
          {(!coverage.total_scanned || coverage.total_scanned === 0) && (
            <p className="text-xs text-ink-500 mt-3">
              No coverage data yet. Run a GitHub scan from the Coverage Center.
            </p>
          )}
        </Card>

        {/* Recent changes feed */}
        <Card title="Recent Changes" eyebrow="Live Feed" className="lg:col-span-1">
          {recentChanges.length === 0 ? (
            <div className="text-sm text-ink-500">No requirement changes detected yet.</div>
          ) : (
            <div className="space-y-3">
              {recentChanges.map((c) => (
                <div key={c.id} className="border-b border-base-500 last:border-0 pb-3 last:pb-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono uppercase text-ink-500">
                      {c.change_type.replace("_", " ")}
                    </span>
                    {c.risk_level && <RiskBadge level={c.risk_level} score={c.risk_score} size="sm" />}
                  </div>
                  <div className="text-sm text-ink-100 line-clamp-2">
                    {c.risk_justification || "No justification recorded."}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
}

function CoverageRow({ label, value, color }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2 text-sm text-ink-300">
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
        {label}
      </div>
      <span className="font-mono text-sm text-ink-100">{value}</span>
    </div>
  );
}
