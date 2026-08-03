import { useEffect, useState } from "react";
import { Target, RefreshCw, CheckCircle, AlertCircle, XCircle } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import { useProject } from "../context/ProjectContext";
import { github } from "../api/client";

const STATUS_CONFIG = {
  fully_implemented:     { label: "Fully Implemented",    color: "#4ADE80", icon: CheckCircle },
  partially_implemented: { label: "Partially Implemented", color: "#FBBF24", icon: AlertCircle },
  not_implemented:       { label: "Not Implemented",       color: "#F87171", icon: XCircle },
};

function CoverageBar({ percent, status }) {
  const color = status === "fully_implemented" ? "#4ADE80"
    : status === "partially_implemented" ? "#FBBF24" : "#F87171";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-base-500 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${percent}%`, backgroundColor: color }}/>
      </div>
      <span className="text-xs font-mono w-10 text-right" style={{ color }}>{percent}%</span>
    </div>
  );
}

export default function CoverageCenter() {
  const { currentProject } = useProject();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [expandedId, setExpandedId] = useState(null);

  const load = () => {
    if (!currentProject) return;
    setLoading(true);
    github.coverage(currentProject.id)
      .then(res => setData(res.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [currentProject]);

  const reqs = data?.requirements || [];
  const filtered = filter === "all" ? reqs : reqs.filter(r => r.status === filter);

  return (
    <Layout title="Coverage Center">
      {/* Header stats */}
      {data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
          <div className="bg-base-700 border border-base-500 rounded-lg p-4 text-center">
            <div className="text-2xl font-mono font-bold text-ink-100">{data.overall_coverage_percent}%</div>
            <div className="text-xs font-mono text-ink-500 mt-1">OVERALL</div>
          </div>
          {Object.entries(STATUS_CONFIG).map(([key, { label, color }]) => (
            <div key={key} className="bg-base-700 border border-base-500 rounded-lg p-4 text-center">
              <div className="text-2xl font-mono font-bold" style={{ color }}>
                {data[key.replace("fully_implemented","fully_implemented").replace("partially_implemented","partially_implemented").replace("not_implemented","not_implemented")] ?? (key === "fully_implemented" ? data.fully_implemented : key === "partially_implemented" ? data.partially_implemented : data.not_implemented)}
              </div>
              <div className="text-xs font-mono text-ink-500 mt-1 leading-tight">{label.toUpperCase()}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-2 mb-4">
        {["all", "fully_implemented", "partially_implemented", "not_implemented"].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded text-xs font-mono uppercase tracking-wider border transition-colors ${
              filter === f ? "bg-signal/10 text-signal border-signal/30" : "bg-base-700 text-ink-500 border-base-500 hover:text-ink-100"
            }`}>
            {f === "all" ? "All" : STATUS_CONFIG[f].label}
          </button>
        ))}
        <button onClick={load} className="ml-auto p-1.5 rounded bg-base-700 border border-base-500 text-ink-500 hover:text-ink-100 transition-colors">
          <RefreshCw size={14}/>
        </button>
      </div>

      {loading ? (
        <Card><div className="text-sm text-ink-500 py-4 text-center">Loading coverage data...</div></Card>
      ) : !data || reqs.length === 0 ? (
        <Card>
          <div className="flex flex-col items-center py-10 text-center">
            <Target size={32} className="text-ink-500 mb-3"/>
            <p className="text-sm text-ink-300 mb-1">No coverage data yet.</p>
            <p className="text-xs text-ink-500">Run a scan from the GitHub Center first.</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-2">
          {filtered.map(req => {
            const cfg = STATUS_CONFIG[req.status] || STATUS_CONFIG.not_implemented;
            const Icon = cfg.icon;
            const expanded = expandedId === req.requirement_id;
            return (
              <div key={req.requirement_id}
                className="bg-base-700 border border-base-500 rounded-lg hover:border-signal/30 transition-colors cursor-pointer"
                onClick={() => setExpandedId(expanded ? null : req.requirement_id)}>
                <div className="px-4 py-3">
                  <div className="flex items-start gap-3">
                    <Icon size={16} className="mt-0.5 shrink-0" style={{ color: cfg.color }}/>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-ink-100 line-clamp-2">{req.requirement_text}</p>
                      <div className="mt-2">
                        <CoverageBar percent={req.coverage_percent} status={req.status}/>
                      </div>
                    </div>
                  </div>
                </div>
                {expanded && (
                  <div className="border-t border-base-500 px-4 py-3 grid sm:grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs font-mono text-risk-low mb-2">FOUND</div>
                      {req.found_implementations?.length > 0
                        ? req.found_implementations.map((f, i) => (
                            <div key={i} className="text-xs text-ink-300 flex items-start gap-1 mb-1">
                              <span className="text-risk-low mt-0.5">+</span>{f}
                            </div>))
                        : <p className="text-xs text-ink-500">Nothing found yet.</p>}
                    </div>
                    <div>
                      <div className="text-xs font-mono text-risk-critical mb-2">MISSING</div>
                      {req.missing_implementations?.length > 0
                        ? req.missing_implementations.map((m, i) => (
                            <div key={i} className="text-xs text-ink-300 flex items-start gap-1 mb-1">
                              <span className="text-risk-critical mt-0.5">−</span>{m}
                            </div>))
                        : <p className="text-xs text-ink-500">Nothing missing.</p>}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </Layout>
  );
}
