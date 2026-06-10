/**
 * Centralized API client with JWT auth injection and error handling.
 */
import axios, { AxiosInstance, AxiosResponse } from "axios";
import type {
  DashboardData,
  ExecutiveReport,
  Application,
  ScanRequest,
  CoverageReport,
  FailureAnalysis,
  MigrationReport,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

function createApiClient(): AxiosInstance {
  const client = axios.create({ baseURL: BASE_URL, timeout: 120000 });

  client.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  client.interceptors.response.use(
    (res) => res,
    (err) => {
      if (err.response?.status === 401) {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      }
      return Promise.reject(err);
    }
  );

  return client;
}

const api = createApiClient();

// ── Auth ───────────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    api.post<{ access_token: string; refresh_token: string }>(
      `/auth/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
    ),
  register: (payload: {
    email: string;
    username: string;
    password: string;
    role?: string;
  }) => api.post("/auth/register", payload),
};

// ── Applications ───────────────────────────────────────────────────────────

export const applicationsApi = {
  list: (params?: { skip?: number; limit?: number; business_unit?: string; domain?: string }) =>
    api.get<Application[]>("/dashboard/applications", { params }),
  scan: (payload: ScanRequest) => api.post("/scan", payload),
  bulkScan: (repo_paths: string[], ai_provider = "groq") =>
    api.post("/scan/bulk", { repo_paths, ai_provider }),
};

// ── MUnit Generation ───────────────────────────────────────────────────────

export const munitApi = {
  generate: (payload: {
    application_id: string;
    test_types?: string[];
    target_coverage?: number;
    ai_provider?: string;
  }) => api.post("/generate-munit", payload),
};

// ── Execution ──────────────────────────────────────────────────────────────

export const executionApi = {
  run: (payload: {
    application_id: string;
    environment?: string;
    maven_command?: string;
  }) => api.post("/execute-tests", payload),
};

// ── Coverage ───────────────────────────────────────────────────────────────

export const coverageApi = {
  analyze: (application_id: string, test_run_id?: string) =>
    api.post<CoverageReport>("/coverage", { application_id, test_run_id }),
  getLatest: (application_id: string) =>
    api.get<CoverageReport>(`/coverage/${application_id}`),
};

// ── Failures ───────────────────────────────────────────────────────────────

export const failuresApi = {
  analyze: (test_run_id: string, ai_provider = "groq") =>
    api.post<{ analyses: FailureAnalysis[]; summary: Record<string, number> }>(
      "/analyze-failures",
      { test_run_id, ai_provider }
    ),
};

// ── Migration ──────────────────────────────────────────────────────────────

export const migrationApi = {
  analyze: (payload: {
    application_id: string;
    target_version?: string;
    source_version?: string;
    ai_provider?: string;
  }) => api.post<MigrationReport>("/migration-analysis", payload),
};

// ── Dashboard ──────────────────────────────────────────────────────────────

export const dashboardApi = {
  get: () => api.get<DashboardData>("/dashboard"),
};

// ── Executive Reports ──────────────────────────────────────────────────────

export const reportsApi = {
  getExecutive: () => api.get<ExecutiveReport>("/executive-report"),
  getApplicationReport: (application_id: string) =>
    api.get(`/executive-report/application/${application_id}`),
  downloadPdf: (application_id: string) =>
    api.get(`/executive-report/pdf/${application_id}`, { responseType: "blob" }),
};

export default api;
