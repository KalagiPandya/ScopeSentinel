import { useEffect, useState } from "react";
import { FileText, Download, Printer } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import RiskBadge from "../components/RiskBadge";
import { useProject } from "../context/ProjectContext";
import { analytics, changes as changesApi, requirements as reqApi, github } from "../api/client";

export default function Reports() {
  const { currentProject } = useProject();
  const [summary, setSummary] = useState(null);
  const [changeList, setChangeList] = useState([]);
  const [reqCount, setReqCount] = useState(0);
  const [coverage, setCoverage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!currentProject) return;
    setLoading(true);
    Promise.all([
      analytics.summary(currentProject.id),
      changesApi.listByProject(currentProject.id),
      reqApi.listByProject(currentProject.id),
      github.coverage(currentProject.id).catch(() => ({ data: null })),
    ]).then(([s, c, r, cov]) => {
      setSummary(s.data);
      setChangeList(c.data);
      setReqCount(r.data.length);
      setCoverage(cov.data);
    }).finally(() => setLoading(false));
  }, [currentProject]);

  const handlePrint = () => window.print();

  const handleDownloadJSON = () => {
    const report = { project: currentProject?.name, generated_at: new Date().toISOString(), summary, changes: changeList, coverage };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `scopesentinel-report-${currentProject?.name?.replace(/\s+/g, "-")}.json`;
    a.click(); URL.revokeObjectURL(url);
  };

  if (loading) {
    return <Layout title="Reports"><Card><div className="text-sm text-ink-500 py-4 text-center">Generating report...</div></Card></Layout>;
  }

  const riskDist = summary?.risk_distribution || {};
  const cov = summary?.coverage || {};

  return (
    <Layout title="Reports">
      <div className="flex justify-end gap-2 mb-4 print:hidden">
        <button onClick={handleDownloadJSON} className="flex items-center gap-2 bg-base-700 border border-base-500 text-ink-100 text-sm px-3 py-2 rounded hover:border-signal/40 transition-colors">
          <Download size={14}/> Export JSON
        </button>
        <button onClick={handlePrint} className="flex items-center gap-2 bg-signal text-base-900 font-semibold text-sm px-3 py-2 rounded hover:bg-signal/90 transition-colors">
          <Printer size={14}/> Print / Save as PDF
        </button>
      </div>

      <Card>
        <div className="text-center mb-6 pb-4 border-b border-base-500">
          <div className="flex items-center justify-center gap-2 mb-2">
            <FileText size={20} className="text-signal"/>
            <h2 className="text-lg font-semibold text-ink-100">ScopeSentinel Project Report</h2>
          </div>
          <p className="text-sm text-ink-300">{currentProject?.name}</p>
          <p className="text-xs font-mono text-ink-500 mt-1">Generated {new Date().toLocaleString()}</p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <ReportStat label="Total Requirements" value={reqCount}/>
          <ReportStat label="Total Changes" value={summary?.total_changes ?? 0}/>
          <ReportStat label="Avg Coverage" value={`${cov.average_percent ?? 0}%`}/>
          <ReportStat label="High+Critical Risk" value={(riskDist.high || 0) + (riskDist.critical || 0)}/>
        </div>

        <div className="grid sm:grid-cols-2 gap-6 mb-6">
          <div>
            <h3 className="text-sm font-semibold text-ink-100 mb-2">Risk Distribution</h3>
            <div className="space-y-1">
              {["critical", "high", "medium", "low"].map(l => (
                <div key={l} className="flex justify-between text-sm">
                  <span className="text-ink-300 capitalize">{l}</span>
                  <span className="font-mono text-ink-100">{riskDist[l] || 0}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-ink-100 mb-2">Coverage Breakdown</h3>
            <div className="space-y-1">
              <div className="flex justify-between text-sm"><span className="text-ink-300">Fully implemented</span><span className="font-mono text-ink-100">{cov.fully_implemented || 0}</span></div>
              <div className="flex justify-between text-sm"><span className="text-ink-300">Partially implemented</span><span className="font-mono text-ink-100">{cov.partially_implemented || 0}</span></div>
              <div className="flex justify-between text-sm"><span className="text-ink-300">Not implemented</span><span className="font-mono text-ink-100">{cov.not_implemented || 0}</span></div>
            </div>
          </div>
        </div>

        <h3 className="text-sm font-semibold text-ink-100 mb-2">Recent Requirement Changes</h3>
        {changeList.length === 0 ? (
          <p className="text-sm text-ink-500">No changes recorded.</p>
        ) : (
          <div className="space-y-2">
            {changeList.slice(0, 15).map(c => (
              <div key={c.id} className="flex items-center justify-between text-sm py-2 border-b border-base-500 last:border-0">
                <div className="flex-1 min-w-0">
                  <span className="text-xs font-mono text-ink-500 uppercase mr-2">{c.change_type?.replace("_", " ")}</span>
                  <span className="text-ink-300 truncate">{c.risk_justification || "—"}</span>
                </div>
                {c.risk_level && <RiskBadge level={c.risk_level} score={c.risk_score} size="sm"/>}
              </div>
            ))}
          </div>
        )}
      </Card>
    </Layout>
  );
}

function ReportStat({ label, value }) {
  return (
    <div className="text-center bg-base-600 rounded-lg p-3">
      <div className="text-xl font-mono font-bold text-ink-100">{value}</div>
      <div className="text-[10px] font-mono text-ink-500 uppercase mt-1">{label}</div>
    </div>
  );
}
