import { useState } from "react";
import { ChevronDown, LogOut, User } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useProject } from "../context/ProjectContext";

export default function TopBar({ title }) {
  const { user, logout } = useAuth();
  const { projectList, currentProject, selectProject } = useProject();
  const [projectOpen, setProjectOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);

  return (
    <header className="h-16 border-b border-base-500 bg-base-900/80 backdrop-blur sticky top-0 z-10 flex items-center justify-between px-6">
      <h1 className="text-lg font-semibold text-ink-100">{title}</h1>

      <div className="flex items-center gap-3">
        {/* Project switcher */}
        <div className="relative">
          <button
            onClick={() => setProjectOpen((o) => !o)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-base-700 border border-base-500 text-sm text-ink-100 hover:border-signal/40 transition-colors"
          >
            <span className="font-mono text-xs text-ink-500">PROJECT</span>
            <span className="font-medium">{currentProject?.name || "No project"}</span>
            <ChevronDown size={14} className="text-ink-500" />
          </button>
          {projectOpen && (
            <div className="absolute right-0 mt-2 w-64 bg-base-700 border border-base-500 rounded-md shadow-panel py-1 z-20">
              {projectList.length === 0 && (
                <div className="px-3 py-2 text-sm text-ink-500">No projects found</div>
              )}
              {projectList.map((p) => (
                <button
                  key={p.id}
                  onClick={() => {
                    selectProject(p);
                    setProjectOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-base-600 transition-colors ${
                    currentProject?.id === p.id ? "text-signal" : "text-ink-100"
                  }`}
                >
                  {p.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setUserOpen((o) => !o)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-base-700 border border-base-500 text-sm text-ink-100 hover:border-signal/40 transition-colors"
          >
            <User size={14} />
            <span>{user?.name}</span>
            <ChevronDown size={14} className="text-ink-500" />
          </button>
          {userOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-base-700 border border-base-500 rounded-md shadow-panel py-1 z-20">
              <div className="px-3 py-2 text-xs text-ink-500 border-b border-base-500">
                <div className="font-mono uppercase">{user?.role}</div>
                <div className="truncate">{user?.email}</div>
              </div>
              <button
                onClick={logout}
                className="w-full flex items-center gap-2 text-left px-3 py-2 text-sm text-risk-high hover:bg-base-600 transition-colors"
              >
                <LogOut size={14} />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
