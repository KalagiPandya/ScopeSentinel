import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  ListChecks,
  GitBranch,
  Upload,
  Network,
  ShieldAlert,
  Github,
  Target,
  GitPullRequest,
  Bell,
  Users,
  FileText,
  Settings,
  Radio,
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/requirements", label: "Requirement Center", icon: ListChecks },
  { to: "/changes", label: "Change Center", icon: GitBranch },
  { to: "/upload", label: "Upload Center", icon: Upload },
  { to: "/impact", label: "Impact Graph", icon: Network },
  { to: "/risk", label: "Risk Center", icon: ShieldAlert },
  { to: "/github", label: "GitHub Center", icon: Github },
  { to: "/coverage", label: "Coverage Center", icon: Target },
  { to: "/pr-review", label: "PR Review Center", icon: GitPullRequest },
  { to: "/notifications", label: "Notifications", icon: Bell },
  { to: "/team", label: "Team Management", icon: Users },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="w-60 bg-base-800 border-r border-base-500 flex flex-col h-screen sticky top-0 shrink-0">
      <div className="flex items-center gap-2 px-5 h-16 border-b border-base-500">
        <Radio size={20} className="text-signal" />
        <div>
          <div className="font-mono font-bold text-sm text-ink-100 leading-tight">ScopeSentinel</div>
          <div className="font-mono text-[10px] text-ink-500 leading-tight">v2.0</div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? "bg-signal/10 text-signal border border-signal/20"
                  : "text-ink-300 hover:text-ink-100 hover:bg-base-600 border border-transparent"
              }`
            }
          >
            <Icon size={16} strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-3 border-t border-base-500">
        <div className="text-[10px] font-mono text-ink-500 uppercase tracking-wider">
          AI Requirement Guardian
        </div>
      </div>
    </aside>
  );
}
