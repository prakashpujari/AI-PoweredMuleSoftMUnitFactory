"""GET /executive-report — full platform executive report with PDF download."""
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, func

from app.agents.executive_reporting_agent import ExecutiveReportingAgent
from app.api.deps import DBSession, ReadUser
from app.models.application import Application
from app.models.test_run import TestRun
from app.models.coverage_report import CoverageReport
from app.models.failure_report import FailureReport
from app.models.migration_report import MigrationReport
from app.utils.logging import get_logger

router = APIRouter(prefix="/executive-report", tags=["reports"])
logger = get_logger(__name__)


@router.get("", response_model=dict)
async def get_executive_report(
    db: DBSession,
    _user: ReadUser,
) -> dict:
    """Generate a full executive report across all applications."""

    # Platform totals
    apps = (await db.execute(select(Application))).scalars().all()
    total_apps = len(apps)
    tested_apps = sum(1 for a in apps if str(a.status) in ("tested", "analyzed"))

    run_stats = await db.execute(
        select(
            func.sum(TestRun.total_tests),
            func.sum(TestRun.passed_tests),
            func.sum(TestRun.failed_tests),
        )
    )
    row = run_stats.one()
    total_executed = int(row[0] or 0)
    total_passed = int(row[1] or 0)
    total_failed = int(row[2] or 0)
    pass_rate = (total_passed / total_executed * 100) if total_executed else 0.0

    avg_cov = await db.scalar(select(func.avg(Application.coverage_score))) or 0.0
    avg_security = await db.scalar(select(func.avg(Application.security_score))) or 0.0
    avg_perf = await db.scalar(select(func.avg(Application.performance_score))) or 0.0
    avg_readiness = await db.scalar(select(func.avg(Application.production_readiness_score))) or 0.0
    avg_risk = await db.scalar(select(func.avg(Application.risk_score))) or 0.0
    avg_migration = await db.scalar(select(func.avg(Application.migration_readiness_score))) or 0.0

    # Business unit breakdown
    bu_stats = await db.execute(
        select(Application.business_unit, func.count(Application.id), func.avg(Application.coverage_score))
        .group_by(Application.business_unit)
    )
    bu_breakdown = [
        {"business_unit": row[0] or "Unknown", "count": row[1], "avg_coverage": round(float(row[2] or 0), 1)}
        for row in bu_stats
    ]

    # Domain breakdown
    domain_stats = await db.execute(
        select(Application.domain, func.count(Application.id), func.avg(Application.production_readiness_score))
        .group_by(Application.domain)
    )
    domain_breakdown = [
        {"domain": row[0] or "Unknown", "count": row[1], "avg_readiness": round(float(row[2] or 0), 1)}
        for row in domain_stats
    ]

    # API type breakdown
    api_stats = await db.execute(
        select(Application.api_type, func.count(Application.id))
        .group_by(Application.api_type)
    )
    api_breakdown = [
        {"api_type": str(row[0]), "count": row[1]}
        for row in api_stats
    ]

    # Risk scoring
    def risk_level(score: float) -> str:
        if score < 20: return "LOW"
        if score < 50: return "MEDIUM"
        if score < 75: return "HIGH"
        return "CRITICAL"

    def recommendation(readiness: float, risk: float) -> str:
        if readiness >= 90 and risk < 20:
            return "APPROVED FOR PRODUCTION"
        if readiness >= 75 and risk < 40:
            return "CONDITIONAL APPROVAL"
        if readiness >= 60:
            return "ADDITIONAL TESTING REQUIRED"
        return "NOT READY FOR PRODUCTION"

    confidence_score = min(
        (avg_cov / 100 * 0.4 + pass_rate / 100 * 0.4 + avg_security / 100 * 0.2),
        1.0,
    )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_version": "1.0",
        "applications_scanned": total_apps,
        "applications_tested": tested_apps,
        "tests_executed": total_executed,
        "tests_passed": total_passed,
        "tests_failed": total_failed,
        "pass_rate": round(pass_rate, 1),
        "coverage_percent": round(float(avg_cov), 1),
        "security_score": round(float(avg_security), 1),
        "performance_score": round(float(avg_perf), 1),
        "production_readiness": round(float(avg_readiness), 1),
        "migration_readiness": round(float(avg_migration), 1),
        "risk_level": risk_level(float(avg_risk)),
        "recommendation": recommendation(float(avg_readiness), float(avg_risk)),
        "confidence_score": round(confidence_score, 2),
        "business_unit_breakdown": bu_breakdown,
        "domain_breakdown": domain_breakdown,
        "api_type_breakdown": api_breakdown,
    }

    logger.info("executive_report_generated", apps=total_apps, readiness=avg_readiness)
    return report


@router.get("/application/{application_id}", response_model=dict)
async def get_application_report(
    application_id: str,
    db: DBSession,
    _user: ReadUser,
) -> dict:
    """Generate executive report for a single application."""
    app_id = uuid.UUID(application_id)
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Latest test run
    run_result = await db.execute(
        select(TestRun)
        .where(TestRun.application_id == app_id)
        .order_by(TestRun.created_at.desc())
        .limit(1)
    )
    latest_run = run_result.scalar_one_or_none()

    # Latest coverage
    cov_result = await db.execute(
        select(CoverageReport)
        .where(CoverageReport.application_id == app_id)
        .order_by(CoverageReport.created_at.desc())
        .limit(1)
    )
    coverage = cov_result.scalar_one_or_none()

    # Latest migration
    mig_result = await db.execute(
        select(MigrationReport)
        .where(MigrationReport.application_id == app_id)
        .order_by(MigrationReport.created_at.desc())
        .limit(1)
    )
    migration = mig_result.scalar_one_or_none()

    # Run executive reporting agent for single app
    agent = ExecutiveReportingAgent()
    state = await agent.run({
        "app_metadata": {"name": app.name, "id": str(app.id)},
        "execution_summary": {
            "total_tests": latest_run.total_tests if latest_run else 0,
            "passed": latest_run.passed_tests if latest_run else 0,
            "failed": latest_run.failed_tests if latest_run else 0,
            "skipped": latest_run.skipped_tests if latest_run else 0,
            "pass_rate": latest_run.pass_rate if latest_run else 0.0,
        },
        "coverage_report": {
            "overall_coverage": coverage.overall_coverage if coverage else 0,
            "flow_coverage": coverage.flow_coverage if coverage else 0,
            "processor_coverage": coverage.processor_coverage if coverage else 0,
            "error_handler_coverage": coverage.error_handler_coverage if coverage else 0,
            "meets_target": coverage.meets_target if coverage else False,
            "coverage_gaps": coverage.coverage_gaps if coverage else [],
            "ai_recommendations": coverage.ai_recommendations if coverage else "",
        },
        "failure_summary": {},
        "failure_analyses": [],
        "migration_report": {
            "source_version": migration.source_version if migration else "",
            "target_version": migration.target_version if migration else "",
            "overall_risk": migration.overall_risk.value if migration else "unknown",
            "migration_readiness_score": migration.migration_readiness_score if migration else 0,
            "estimated_effort_days": migration.estimated_effort_days if migration else 0,
        },
        "flows": [],
        "test_cases": [],
        "config": {},
    })

    return {
        "application_id": str(app.id),
        "application_name": app.name,
        "report": state.get("dashboard_data", {}),
        "executive_summary": state.get("executive_summary", ""),
        "scores": state.get("scores", {}),
        "pdf_report_path": state.get("pdf_report_path", ""),
    }


@router.get("/pdf/{application_id}")
async def download_pdf_report(
    application_id: str,
    db: DBSession,
    _user: ReadUser,
) -> FileResponse:
    """Download PDF executive report for an application."""
    app_id = uuid.UUID(application_id)
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    pdf_path = Path(app.repo_path or "/tmp") / "target" / "ai-munit-factory-report.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF report not yet generated. Run /executive-report/application/{id} first.")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{app.name}-munit-report.pdf",
    )
