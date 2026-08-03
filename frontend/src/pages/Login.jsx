import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Radio } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("pm@scopesentinel.com");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-base-900 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 justify-center mb-8">
          <Radio size={28} className="text-signal" />
          <div className="text-center">
            <div className="font-mono font-bold text-xl text-ink-100">ScopeSentinel</div>
            <div className="font-mono text-xs text-ink-500 tracking-wider">AI REQUIREMENT GUARDIAN</div>
          </div>
        </div>

        <div className="bg-base-700 border border-base-500 rounded-lg shadow-panel p-6">
          <h2 className="text-sm font-semibold text-ink-100 mb-4">Sign in</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-ink-500 mb-1.5">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-base-600 border border-base-500 rounded-md px-3 py-2 text-sm text-ink-100 focus:border-signal/50 outline-none transition-colors"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-ink-500 mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-base-600 border border-base-500 rounded-md px-3 py-2 text-sm text-ink-100 focus:border-signal/50 outline-none transition-colors"
                required
              />
            </div>

            {error && (
              <div className="text-sm text-risk-critical bg-risk-critical/10 border border-risk-critical/20 rounded-md px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-signal text-base-900 font-semibold text-sm py-2 rounded-md hover:bg-signal/90 transition-colors disabled:opacity-50"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <div className="mt-4 pt-4 border-t border-base-500 text-xs text-ink-500 font-mono">
            <div>Seeded accounts (password: password123)</div>
            <div className="mt-1">pm@scopesentinel.com</div>
            <div>dev@scopesentinel.com</div>
            <div>qa@scopesentinel.com</div>
          </div>
        </div>
      </div>
    </div>
  );
}
