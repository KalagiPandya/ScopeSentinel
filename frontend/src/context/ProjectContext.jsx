import { createContext, useContext, useState, useEffect } from "react";
import { projects as projectsApi } from "../api/client";
import { useAuth } from "./AuthContext";

const ProjectContext = createContext(null);

export function ProjectProvider({ children }) {
  const { user } = useAuth();
  const [projectList, setProjectList] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    projectsApi
      .list()
      .then((res) => {
        setProjectList(res.data);
        const savedId = localStorage.getItem("scopesentinel_project_id");
        const found = res.data.find((p) => p.id === savedId);
        setCurrentProject(found || res.data[0] || null);
      })
      .finally(() => setLoading(false));
  }, [user]);

  const selectProject = (project) => {
    setCurrentProject(project);
    localStorage.setItem("scopesentinel_project_id", project.id);
  };

  return (
    <ProjectContext.Provider value={{ projectList, currentProject, selectProject, loading, setProjectList }}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error("useProject must be used within ProjectProvider");
  return ctx;
}
