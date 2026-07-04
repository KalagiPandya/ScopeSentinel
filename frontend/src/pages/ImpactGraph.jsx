import { useEffect, useState } from "react";
import { Network, Zap } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import { useProject } from "../context/ProjectContext";
import { requirements as reqApi, impact as impactApi } from "../api/client";

const TYPE_COLOR = { frontend: "#3B9EFF", backend: "#A78BFA", database: "#4ADE80", test: "#FBBF24", config: "#9BAAB9", default: "#6B7A8D" };
const DEPTH_LABELS = { depth_1: "Direct (HIGH)", depth_2: "Indirect (MEDIUM)", depth_3: "Distant (LOW)" };
const DEPTH_COLORS = { depth_1: "#F87171", depth_2: "#FBBF24", depth_3: "#4ADE80" };

export default function ImpactGraph() {
  const { currentProject } = useProject();
  const [reqs, setReqs] = useState([]);
  const [selectedReq, setSelectedReq] = useState(null);
  const [impactData, setImpactData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (!currentProject) return;
    reqApi.listByProject(currentProject.id).then(r => setReqs(r.data)).catch(() => {});
    impactApi.stats(currentProject.id).then(r => setStats(r.data)).catch(() => {});
  }, [currentProject]);

  const runAnalysis = async (req) => {
    setSelectedReq(req); setLoading(true); setImpactData(null);
    try {
      const res = await impactApi.analyze({ requirement_id: req.id, max_depth: 3 });
      setImpactData(res.data);
    } catch (e) {
      setImpactData({ error: e.response?.data?.detail || "Analysis failed" });
    } finally { setLoading(false); }
  };

  return (
    <Layout title="Impact Graph">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card title="Select Requirement" eyebrow="BFS Impact Analysis" className="lg:col-span-1">
          {stats && (
            <div className="flex gap-4 mb-3 text-xs font-mono">
              <span className="text-ink-300">{stats.graph_stats?.requirements || 0} <span className="text-ink-500">nodes</span></span>
              <span className="text-ink-300">{stats.graph_stats?.modules || 0} <span className="text-ink-500">modules</span></span>
            </div>
          )}
          <div className="space-y-1 max-h-96 overflow-y-auto pr-1">
            {reqs.length === 0 && <p className="text-xs text-ink-500">No requirements loaded.</p>}
            {reqs.map(r => (
              <button key={r.id} onClick={() => runAnalysis(r)}
                className={`w-full text-left px-3 py-2 rounded text-xs transition-colors border ${
                  selectedReq?.id === r.id ? "bg-signal/10 border-signal/30 text-signal" : "bg-base-600 border-transparent text-ink-300 hover:border-base-500 hover:text-ink-100"
                }`}>
                <span className="line-clamp-2">{r.text}</span>
              </button>
            ))}
          </div>
        </Card>

        <div className="lg:col-span-2">
          {loading && (
            <Card>
              <div className="flex items-center justify-center py-12 text-ink-500 text-sm gap-2">
                <Zap size={16} className="text-signal animate-pulse"/> Running BFS traversal...
              </div>
            </Card>
          )}

          {impactData?.error && (
            <Card><p className="text-sm text-risk-critical">{impactData.error}</p></Card>
          )}

          {impactData && !impactData.error && (
            <div className="space-y-4">
              <Card title="Impact Summary" eyebrow={selectedReq?.text?.slice(0, 60) + "..."}>
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-mono font-bold text-ink-100">{impactData.impact?.total_affected || 0}</div>
                    <div className="text-xs font-mono text-ink-500 mt-1">TOTAL AFFECTED</div>
                  </div>
                  <div className="text-sm text-ink-300">{impactData.summary}</div>
                </div>
              </Card>

              {["depth_1", "depth_2", "depth_3"].map(depthKey => {
                const modules = impactData.impact?.[depthKey] || [];
                if (!modules.length) return null;
                return (
                  <Card key={depthKey} title={DEPTH_LABELS[depthKey]}
                    eyebrow={`${modules.length} module${modules.length !== 1 ? "s" : ""}`}>
                    <div className="flex flex-wrap gap-2">
                      {modules.map((m, i) => (
                        <div key={i} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs"
                          style={{ borderColor: `${TYPE_COLOR[m.type] || TYPE_COLOR.default}40`, color: TYPE_COLOR[m.type] || TYPE_COLOR.default, backgroundColor: `${TYPE_COLOR[m.type] || TYPE_COLOR.default}10` }}>
                          <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: DEPTH_COLORS[depthKey] }}/>
                          {m.name}
                          <span className="opacity-60 text-[10px]">{m.type}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                );
              })}
            </div>
          )}

          {!selectedReq && !loading && (
            <Card>
              <div className="flex flex-col items-center py-10 text-center">
                <Network size={32} className="text-ink-500 mb-3"/>
                <p className="text-sm text-ink-300 mb-1">Select a requirement from the list.</p>
                <p className="text-xs text-ink-500">Neo4j BFS will find all modules affected by a change to that requirement.</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </Layout>
  );
}
