import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { ShieldAlert } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import RiskBadge, { RISK_COLORS } from "../components/RiskBadge";
import { useProject } from "../context/ProjectContext";
import { changes as changesApi, analytics } from "../api/client";

export default function RiskCenter() {
  const { currentProject } = useProject();
  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    if (!currentProject) return;
    setLoading(true);
    Promise.all([changesApi.listByProject(currentProject.id), analytics.summary(currentProject.id)])
      .then(([ch, sum]) => { setItems(ch.data); setSummary(sum.data); })
      .finally(() => setLoading(false));
  }, [currentProject]);

  const withRisk = items.filter(c => c.risk_level);
  const filtered = filter === "all" ? withRisk : withRisk.filter(c => c.risk_level === filter);

  const dist = summary?.risk_distribution || {};
  const barData = ["low", "medium", "high", "critical"].map(l => ({ name: l, count: dist[l] || 0, fill: RISK_COLORS[l] }));

  return (
    <Layout title="Risk Center">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-5">
        {["critical", "high", "medium", "low"].map(level => (
          <div key={level} className="bg-base-700 border border-base-500 rounded-lg p-4 flex items-center gap-3">
            <span className="pulse-dot" style={{ backgroundColor: RISK_COLORS[level] }}/>
            <div>
              <div className="text-xl font-mono font-bold" style={{ color: RISK_COLORS[level] }}>{dist[level] || 0}</div>
              <div className="text-xs font-mono text-ink-500 uppercase">{level}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card title="Risk Distribution" eyebrow="All Changes" className="lg:col-span-1">
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} layout="vertical" margin={{ left: 8, right: 16 }}>
                <XAxis type="number" tick={{ fill: "#6B7A8D", fontSize: 11 }} axisLine={false} tickLine={false}/>
                <YAxis type="category" dataKey="name" tick={{ fill: "#9BAAB9", fontSize: 12, fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} width={60}/>
                <Tooltip contentStyle={{ background: "#131A24", border: "1px solid #26303F", borderRadius: 8, fontSize: 12 }} cursor={{ fill: "#1A222E" }}/>
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {barData.map((d, i) => <Cell key={i} fill={d.fill}/>)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <div className="lg:col-span-2">
          <div className="flex gap-2 mb-3">
            {["all", "critical", "high", "medium", "low"].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded text-xs font-mono uppercase tracking-wider border transition-colors ${
                  filter === f ? "bg-signal/10 text-signal border-signal/30" : "bg-base-700 text-ink-500 border-base-500 hover:text-ink-100"
                }`}>{f}</button>
            ))}
          </div>

          {loading ? (
            <Card><div className="text-sm text-ink-500 py-4 text-center">Loading...</div></Card>
          ) : filtered.length === 0 ? (
            <Card>
              <div className="flex flex-col items-center py-10 text-center">
                <ShieldAlert size={32} className="text-ink-500 mb-3"/>
                <p className="text-sm text-ink-300">No changes with risk data yet.</p>
                <p className="text-xs text-ink-500 mt-1">Run the agent pipeline on a document to generate risk-scored changes.</p>
              </div>
            </Card>
          ) : (
            <div className="space-y-3">
              {filtered.map(c => (
                <Card key={c.id}>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <span className="text-xs font-mono text-ink-500 uppercase">{c.change_type?.replace("_", " ")}</span>
                    <RiskBadge level={c.risk_level} score={c.risk_score}/>
                  </div>
                  <p className="text-sm text-ink-100 mb-2">{c.risk_justification || "No justification recorded."}</p>
                  {c.impact_map?.total_affected > 0 && (
                    <p className="text-xs font-mono text-ink-500">
                      Impact: {c.impact_map.total_affected} module(s) —{" "}
                      {c.impact_map.depth_1?.slice(0, 3).map(m => m.name).join(", ")}
                    </p>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
