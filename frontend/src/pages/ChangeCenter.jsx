import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import RiskBadge from "../components/RiskBadge";
import { useProject } from "../context/ProjectContext";
import { changes as changesApi } from "../api/client";

const CHANGE_TYPE_LABELS = {
  new_addition: "New Addition",
  modification: "Modification",
  deletion: "Deletion",
};

function WordDiff({ wordDiff }) {
  if (!wordDiff?.diff_tokens) return null;
  return (
    <div className="flex flex-wrap gap-1 mt-2 font-mono text-sm leading-relaxed">
      {wordDiff.diff_tokens.map((t, i) => {
        if (t.type === "added") {
          return (
            <span key={i} className="bg-risk-low/15 text-risk-low px-1 rounded">
              {t.word}
            </span>
          );
        }
        if (t.type === "removed") {
          return (
            <span key={i} className="bg-risk-critical/15 text-risk-critical px-1 rounded line-through">
              {t.word}
            </span>
          );
        }
        return <span key={i} className="text-ink-300">{t.word}</span>;
      })}
    </div>
  );
}

export default function ChangeCenter() {
  const { currentProject } = useProject();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    if (!currentProject) return;
    setLoading(true);
    changesApi
      .listByProject(currentProject.id)
      .then((res) => setItems(res.data))
      .finally(() => setLoading(false));
  }, [currentProject]);

  const filtered = items.filter((c) => filter === "all" || c.change_type === filter);

  return (
    <Layout title="Change Center">
      <div className="flex gap-2 mb-4">
        {["all", "new_addition", "modification", "deletion"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-md text-xs font-mono uppercase tracking-wider border transition-colors ${
              filter === f
                ? "bg-signal/10 text-signal border-signal/30"
                : "bg-base-700 text-ink-500 border-base-500 hover:text-ink-100"
            }`}
          >
            {f === "all" ? "All" : CHANGE_TYPE_LABELS[f]}
          </button>
        ))}
      </div>

      {loading ? (
        <Card><div className="text-sm text-ink-500">Loading changes...</div></Card>
      ) : filtered.length === 0 ? (
        <Card>
          <div className="text-sm text-ink-500">
            No changes detected yet. Run the agent pipeline via{" "}
            <code className="font-mono text-ink-300">POST /agent/run</code> on a meeting
            transcript or document to see drift detection in action.
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((c) => (
            <Card key={c.id}>
              <div className="flex items-start justify-between gap-4 mb-2">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-signal bg-signal/10 px-2 py-1 rounded">
                    {CHANGE_TYPE_LABELS[c.change_type]}
                  </span>
                  {c.similarity_score != null && (
                    <span className="ml-2 text-xs font-mono text-ink-500">
                      similarity: {(c.similarity_score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
                {c.risk_level && <RiskBadge level={c.risk_level} score={c.risk_score} />}
              </div>

              {c.word_diff ? (
                <WordDiff wordDiff={c.word_diff} />
              ) : (
                <p className="text-sm text-ink-100 mt-1">New requirement added to baseline.</p>
              )}

              {c.risk_justification && (
                <div className="mt-3 pt-3 border-t border-base-500 text-sm text-ink-300">
                  {c.risk_justification}
                </div>
              )}

              {c.impact_map?.total_affected > 0 && (
                <div className="mt-2 text-xs font-mono text-ink-500">
                  {c.impact_map.total_affected} module(s) affected:{" "}
                  {c.impact_map.depth_1?.map((m) => m.name).join(", ")}
                </div>
              )}

              <div className="mt-2 text-[11px] font-mono text-ink-500">
                detected {new Date(c.detected_at).toLocaleString()}
              </div>
            </Card>
          ))}
        </div>
      )}
    </Layout>
  );
}
