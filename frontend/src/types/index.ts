export interface Application {
  id: string;
  name: string;
  version: string;
  mule_runtime_version: string;
  business_unit: string;
  domain: string;
  api_type: "system" | "process" | "experience" | "unknown";
  status: string;
  flows_count: number;
  coverage_score: number;
  security_score: number;
  performance_score: number;
  quality_score: number;
  production_readiness_score: number;
  migration_readiness_score: number;
  risk_score: number;
  environment: string;
}

export interface DashboardData {
  generated_at: string;
  applications: {
    total_scanned: number;
    total_tested: number;
    meeting_coverage_target: number;
  };
  tests: {
    total_executed: number;
    passed: number;
    failed: number;
    pass_rate: number;
  };
  coverage: {
    average_overall: number;
    target: number;
  };
  scores: {
    production_readiness: number;
    security: number;
    performance: number;
    risk: number;
    coverage: number;
  };
  failures: {
    by_severity: Record<string, number>;
  };
  breakdown: {
    by_api_type: Record<string, number>;
  };
  recent_runs: TestRun[];
}

export interface TestRun {
  id: string;
  run_number: number;
  status: string;
  total: number;
  passed: number;
  failed: number;
  pass_rate: number;
  created_at: string;
}

export interface ExecutiveReport {
  applications_scanned: number;
  applications_tested: number;
  tests_executed: number;
  tests_passed: number;
  tests_failed: number;
  pass_rate: number;
  coverage_percent: number;
  security_score: number;
  performance_score: number;
  production_readiness: number;
  migration_readiness: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  recommendation: string;
  confidence_score: number;
  business_unit_breakdown: { business_unit: string; count: number; avg_coverage: number }[];
  domain_breakdown: { domain: string; count: number; avg_readiness: number }[];
  api_type_breakdown: { api_type: string; count: number }[];
  generated_at: string;
}

export interface ScanRequest {
  repo_path: string;
  business_unit?: string;
  domain?: string;
  environment?: string;
  api_type?: string;
  ai_provider?: string;
}

export interface CoverageReport {
  overall_coverage: number;
  flow_coverage: number;
  processor_coverage: number;
  error_handler_coverage: number;
  meets_target: boolean;
  uncovered_flows: string[];
  coverage_gaps: CoverageGap[];
  ai_recommendations: string;
}

export interface CoverageGap {
  flow: string;
  gap_type: string;
  priority: string;
  recommendation: string;
}

export interface FailureAnalysis {
  test_name: string;
  severity: "critical" | "high" | "medium" | "low";
  root_cause: string;
  suggested_fix: string;
  confidence_score: number;
  is_flaky: boolean;
  failure_category: string;
}

export interface MigrationReport {
  source_version: string;
  target_version: string;
  overall_risk: "low" | "medium" | "high" | "critical";
  migration_readiness_score: number;
  estimated_effort_days: number;
  connector_risks: ConnectorRisk[];
  breaking_changes: string[];
  migration_plan: string;
  recommended_approach: string;
}

export interface ConnectorRisk {
  connector: string;
  risk: string;
  action: string;
  severity: string;
}

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
