import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import { useProject } from "../context/ProjectContext";
import { requirements as requirementsApi } from "../api/client";

const TYPE_COLORS = {
  functional: "#3B9EFF",
  non_functional: "#A78BFA",
  constraint: "#FBBF24",
};

export default function RequirementCenter() {
  const { currentProject } = useProject();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    if (!currentProject) return;
    setLoading(true);
    requirementsApi
      .listByProject(currentProject.id)
      .then((res) => setItems(res.data))
      .finally(() => setLoading(false));
  }, [currentProject]);

  const filtered = items.filter((r) => {
    const matchesQuery = r.text.toLowerCase().includes(query.toLowerCase());
    const matchesType = typeFilter === "all" || r.type === typeFilter;
    return matchesQuery && matchesType;
  });

  return (
    <Layout title="Requirement Center">
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-500" />
          <input
            type="text"
            placeholder="Search requirements..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-base-700 border border-base-500 rounded-md pl-9 pr-3 py-2 text-sm text-ink-100 focus:border-signal/50 outline-none transition-colors"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="bg-base-700 border border-base-500 rounded-md px-3 py-2 text-sm text-ink-100 focus:border-signal/50 outline-none"
        >
          <option value="all">All types</option>
          <option value="functional">Functional</option>
          <option value="non_functional">Non-functional</option>
          <option value="constraint">Constraint</option>
        </select>
      </div>

      <Card eyebrow={`${filtered.length} of ${items.length} requirements`}>
        {loading ? (
          <div className="text-sm text-ink-500">Loading requirements...</div>
        ) : filtered.length === 0 ? (
          <div className="text-sm text-ink-500">No requirements match your search.</div>
        ) : (
          <div className="space-y-2">
            {filtered.map((r) => (
              <div
                key={r.id}
                className="flex items-start gap-3 p-3 rounded-md bg-base-600/40 border border-base-500 hover:border-signal/30 transition-colors"
              >
                <span
                  className="text-[10px] font-mono uppercase px-2 py-1 rounded shrink-0"
                  style={{
                    color: TYPE_COLORS[r.type] || "#9BAAB9",
                    backgroundColor: `${TYPE_COLORS[r.type] || "#9BAAB9"}1A`,
                  }}
                >
                  {r.type.replace("_", " ")}
                </span>
                <div className="flex-1">
                  <p className="text-sm text-ink-100">{r.text}</p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-ink-500 font-mono">
                    <span>source: {r.source || "unknown"}</span>
                    <span>confidence: {(r.confidence_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </Layout>
  );
}
