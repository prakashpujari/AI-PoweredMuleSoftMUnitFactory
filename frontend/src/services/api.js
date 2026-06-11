/**
 * Centralized API client with JWT auth injection and error handling.
 */
import axios from "axios";
const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
function createApiClient() {
    const client = axios.create({ baseURL: BASE_URL, timeout: 120000 });
    client.interceptors.request.use((config) => {
        const token = localStorage.getItem("access_token");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    });
    client.interceptors.response.use((res) => res, (err) => {
        if (err.response?.status === 401) {
            localStorage.removeItem("access_token");
            window.dispatchEvent(new CustomEvent("auth:logout"));
        }
        return Promise.reject(err);
    });
    return client;
}
const api = createApiClient();
// ── Auth ───────────────────────────────────────────────────────────────────
export const authApi = {
    login: (email, password) => api.post(`/auth/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`),
    register: (payload) => api.post("/auth/register", payload),
};
// ── Applications ───────────────────────────────────────────────────────────
export const applicationsApi = {
    list: (params) => api.get("/dashboard/applications", { params }),
    scan: (payload) => api.post("/scan", payload),
    bulkScan: (repo_paths, ai_provider = "groq") => api.post("/scan/bulk", { repo_paths, ai_provider }),
};
// ── MUnit Generation ───────────────────────────────────────────────────────
export const munitApi = {
    generate: (payload) => api.post("/generate-munit", payload),
};
// ── Execution ──────────────────────────────────────────────────────────────
export const executionApi = {
    run: (payload) => api.post("/execute-tests", payload),
};
// ── Coverage ───────────────────────────────────────────────────────────────
export const coverageApi = {
    analyze: (application_id, test_run_id) => api.post("/coverage", { application_id, test_run_id }),
    getLatest: (application_id) => api.get(`/coverage/${application_id}`),
};
// ── Failures ───────────────────────────────────────────────────────────────
export const failuresApi = {
    analyze: (test_run_id, ai_provider = "groq") => api.post("/analyze-failures", { test_run_id, ai_provider }),
};
// ── Migration ──────────────────────────────────────────────────────────────
export const migrationApi = {
    analyze: (payload) => api.post("/migration-analysis", payload),
};
// ── Dashboard ──────────────────────────────────────────────────────────────
export const dashboardApi = {
    get: () => api.get("/dashboard"),
};
// ── Executive Reports ──────────────────────────────────────────────────────
export const reportsApi = {
    getExecutive: () => api.get("/executive-report"),
    getApplicationReport: (application_id) => api.get(`/executive-report/application/${application_id}`),
    downloadPdf: (application_id) => api.get(`/executive-report/pdf/${application_id}`, { responseType: "blob" }),
};
export default api;
