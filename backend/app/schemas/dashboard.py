"""Dashboard and executive report schemas."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class CoverageSummary(BaseModel):
    overall: float
    flow: float
    processor: float
    error_handler: float
    meets_target: bool
    gaps: list[dict] = []


class TestMetrics(BaseModel):
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    pass_rate: float


class Scores(BaseModel):
    security_score: float
    performance_score: float
    quality_score: float
    production_readiness_score: float
    risk_score: float
    overall_grade: str
    recommendation: str
    risk_level: str


class MigrationSummary(BaseModel):
    source_version: str
    target_version: str
    risk: str
    readiness_score: float
    effort_days: int


class DashboardData(BaseModel):
    generated_at: datetime
    application: dict
    test_metrics: TestMetrics
    coverage: CoverageSummary
    scores: Scores
    migration: Optional[MigrationSummary] = None
    top_failures: list[dict] = []
    executive_summary: str = ""
    recommendations: str = ""


class ExecutiveReport(BaseModel):
    """Full executive report matching the specified output format."""
    applications_scanned: int
    applications_tested: int
    tests_executed: int
    tests_passed: int
    tests_failed: int
    pass_rate: float
    coverage_percent: float
    security_score: float
    performance_score: float
    production_readiness: float
    risk_level: str
    recommendation: str
    confidence_score: float
    migration_readiness: float
    business_unit_breakdown: list[dict] = []
    domain_breakdown: list[dict] = []
    api_type_breakdown: list[dict] = []
    environment_breakdown: list[dict] = []
    executive_summary: str = ""
    generated_at: datetime
    report_version: str = "1.0"


class PlatformSummary(BaseModel):
    """Aggregate summary across all 100+ applications."""
    total_applications: int
    tested_applications: int
    total_flows: int
    total_tests_generated: int
    total_tests_executed: int
    overall_pass_rate: float
    average_coverage: float
    applications_meeting_target: int
    high_risk_applications: int
    ready_for_production: int
    pending_migration: int
    critical_failures: int
    generated_at: datetime
