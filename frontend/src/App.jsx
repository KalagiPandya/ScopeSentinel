import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProjectProvider } from "./context/ProjectContext";
import ProtectedRoute from "./components/ProtectedRoute";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import RequirementCenter from "./pages/RequirementCenter";
import ChangeCenter from "./pages/ChangeCenter";
import UploadCenter from "./pages/UploadCenter";
import ImpactGraph from "./pages/ImpactGraph";
import RiskCenter from "./pages/RiskCenter";
import GitHubCenter from "./pages/GitHubCenter";
import CoverageCenter from "./pages/CoverageCenter";
import PRReviewCenter from "./pages/PRReviewCenter";
import Notifications from "./pages/Notifications";
import TeamManagement from "./pages/TeamManagement";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";

function Protected({ children }) {
  return (
    <ProtectedRoute>
      <ProjectProvider>{children}</ProjectProvider>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route path="/" element={<Protected><Dashboard /></Protected>} />
          <Route path="/requirements" element={<Protected><RequirementCenter /></Protected>} />
          <Route path="/changes" element={<Protected><ChangeCenter /></Protected>} />
          <Route path="/upload" element={<Protected><UploadCenter /></Protected>} />
          <Route path="/impact" element={<Protected><ImpactGraph /></Protected>} />
          <Route path="/risk" element={<Protected><RiskCenter /></Protected>} />
          <Route path="/github" element={<Protected><GitHubCenter /></Protected>} />
          <Route path="/coverage" element={<Protected><CoverageCenter /></Protected>} />
          <Route path="/pr-review" element={<Protected><PRReviewCenter /></Protected>} />
          <Route path="/notifications" element={<Protected><Notifications /></Protected>} />
          <Route path="/team" element={<Protected><TeamManagement /></Protected>} />
          <Route path="/reports" element={<Protected><Reports /></Protected>} />
          <Route path="/settings" element={<Protected><Settings /></Protected>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
