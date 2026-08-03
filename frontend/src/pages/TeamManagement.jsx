import { useEffect, useState } from "react";
import { Users, UserPlus } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";
import { auth } from "../api/client";

const ROLE_COLORS = { admin: "#F87171", pm: "#3B9EFF", developer: "#A78BFA", qa: "#4ADE80", analyst: "#FBBF24" };

export default function TeamManagement() {
  const [registerData, setRegisterData] = useState({ name: "", email: "", password: "", role: "developer" });
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true); setStatus("");
    try {
      await auth.register(registerData);
      setStatus(`✓ User "${registerData.name}" created successfully.`);
      setRegisterData({ name: "", email: "", password: "", role: "developer" });
    } catch (err) {
      setStatus(`Error: ${err.response?.data?.detail || "Registration failed"}`);
    } finally { setLoading(false); }
  };

  return (
    <Layout title="Team Management">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="Add Team Member" eyebrow="Register New User">
          <form onSubmit={handleRegister} className="space-y-3">
            {[["name","Name","text","John Doe"],["email","Email","email","dev@company.com"],["password","Password","password","min 8 chars"]].map(([field,label,type,ph]) => (
              <div key={field}>
                <label className="block text-xs font-mono text-ink-500 mb-1">{label.toUpperCase()}</label>
                <input type={type} value={registerData[field]} placeholder={ph} required
                  onChange={e => setRegisterData(d => ({...d, [field]: e.target.value}))}
                  className="w-full bg-base-600 border border-base-500 rounded px-3 py-2 text-sm text-ink-100 focus:border-signal/50 outline-none"/>
              </div>
            ))}
            <div>
              <label className="block text-xs font-mono text-ink-500 mb-1">ROLE</label>
              <select value={registerData.role} onChange={e => setRegisterData(d => ({...d, role: e.target.value}))}
                className="w-full bg-base-600 border border-base-500 rounded px-3 py-2 text-sm text-ink-100 focus:border-signal/50 outline-none">
                {["developer","qa","pm","analyst","admin"].map(r => <option key={r} value={r}>{r.charAt(0).toUpperCase()+r.slice(1)}</option>)}
              </select>
            </div>
            {status && <p className={`text-xs ${status.startsWith("✓") ? "text-risk-low" : "text-risk-critical"}`}>{status}</p>}
            <button type="submit" disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-signal text-base-900 font-semibold text-sm py-2 rounded hover:bg-signal/90 transition-colors disabled:opacity-50">
              <UserPlus size={14}/>{loading ? "Creating..." : "Add Team Member"}
            </button>
          </form>
        </Card>

        <Card title="Seeded Accounts" eyebrow="Available Users">
          <div className="space-y-2">
            {[
              { name: "Rahul Sharma", email: "pm@scopesentinel.com", role: "pm" },
              { name: "Priya Patel", email: "dev@scopesentinel.com", role: "developer" },
              { name: "Amit Singh", email: "qa@scopesentinel.com", role: "qa" },
            ].map(u => (
              <div key={u.email} className="flex items-center gap-3 p-3 bg-base-600 rounded">
                <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-base-900"
                  style={{ backgroundColor: ROLE_COLORS[u.role] }}>
                  {u.name.charAt(0)}
                </div>
                <div>
                  <div className="text-sm text-ink-100">{u.name}</div>
                  <div className="text-xs text-ink-500 font-mono">{u.email}</div>
                </div>
                <span className="ml-auto text-xs font-mono px-2 py-0.5 rounded"
                  style={{ color: ROLE_COLORS[u.role], backgroundColor: `${ROLE_COLORS[u.role]}20` }}>
                  {u.role}
                </span>
              </div>
            ))}
          </div>
          <p className="text-xs text-ink-500 mt-3">All seeded passwords: <code className="font-mono text-signal">password123</code></p>
        </Card>
      </div>
    </Layout>
  );
}
