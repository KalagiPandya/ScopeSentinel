import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("scopesentinel_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("scopesentinel_token");
      localStorage.removeItem("scopesentinel_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default client;

// ── API helper functions ────────────────────────────────────────────────

export const auth = {
  login: (email, password) => client.post("/auth/login", { email, password }),
  register: (data) => client.post("/auth/register", data),
  me: () => client.get("/auth/me"),
};

export const projects = {
  list: () => client.get("/projects/"),
  get: (id) => client.get(`/projects/${id}`),
  create: (data) => client.post("/projects/", data),
  update: (id, data) => client.put(`/projects/${id}`, data),
};

export const requirements = {
  listByProject: (projectId) => client.get(`/requirements/project/${projectId}`),
  get: (id) => client.get(`/requirements/${id}`),
};

export const changes = {
  listByProject: (projectId) => client.get(`/changes/project/${projectId}`),
  get: (id) => client.get(`/changes/${id}`),
};

export const analytics = {
  summary: (projectId) => client.get(`/analytics/project/${projectId}/summary`),
};

export const agent = {
  run: (data) => client.post("/agent/run", data),
};

export const github = {
  scanCoverage: (data) => client.post("/github/scan-coverage", data),
  coverage: (projectId) => client.get(`/github/coverage/project/${projectId}`),
};

export const prReview = {
  run: (data) => client.post("/pr-review/run", data),
};

export const impact = {
  analyze: (data) => client.post("/impact/analyze", data),
  stats: (projectId) => client.get(`/impact/project/${projectId}/stats`),
};

export const search = {
  diff: (oldText, newText) => client.post("/search/diff", { old_text: oldText, new_text: newText }),
  similar: (data) => client.post("/search/similar", data),
  detectChange: (data) => client.post("/search/detect-change", data),
};
