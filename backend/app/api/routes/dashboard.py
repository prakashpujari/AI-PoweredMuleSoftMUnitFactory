"""GET /dashboard — real-time platform metrics and executive KPIs."""
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import select, func

from app.api.deps import DBSession, ReadUser
from app.models.application import Application
from app.models.test_run import TestRun
from app.models.coverage_report import CoverageReport
from app.models.failure_report import FailureReport
from app.utils.logging import get_logger

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
logger = get_logger(__name__)


@router.get("", response_model=dict)
async def get_dashboard(
    db: DBSession,
    _user: ReadUser,
) -> dict:
    """Aggregate platform KPIs across all applications."""

    # Application counts
    total_apps = await db.scalar(select(func.count(Application.id)))
    tested_apps = await db.scalar(
        select(func.count(Application.id)).where(Application.status == "tested")
    )

    # Test run aggregates
    run_stats = await db.execute(
        select(
            func.sum(TestRun.total_tests).label("total"),
            func.sum(TestRun.passed_tests).label("passed"),
            func.sum(TestRun.failed_tests).label("failed"),
            func.avg(TestRun.pass_rate).label("avg_pass_rate"),
        )
    )
    run_row = run_stats.one()
    total_tests = int(run_row.total or 0)
    passed_tests = int(run_row.passed or 0)
    failed_tests = int(run_row.failed or 0)
    avg_pass_rate = float(run_row.avg_pass_rate or 0)

    # Coverage aggregate
    cov_stats = await db.execute(
        select(
            func.avg(CoverageReport.overall_coverage).label("avg_coverage"),
            func.avg(CoverageReport.flow_coverage).label("avg_flow"),
        )
    )
    cov_row = cov_stats.one()
    avg_coverage = float(cov_row.avg_coverage or 0)

    # Score aggregates
    score_stats = await db.execute(
        select(
            func.avg(Application.production_readiness_score).label("readiness"),
            func.avg(Application.security_score).label("security"),
            func.avg(Application.performance_score).label("performance"),
            func.avg(Application.risk_score).label("risk"),
            func.avg(Application.coverage_score).label("coverage"),
        )
    )
    score_row = score_stats.one()

    # Failure severity breakdown
    fail_stats = await db.execute(
        select(
            FailureReport.severity,
            func.count(FailureReport.id).label("count"),
        ).group_by(FailureReport.severity)
    )
    failure_breakdown = {row.severity: row.count for row in fail_stats}

    # API type breakdown
    api_stats = await db.execute(
        select(Application.api_type, func.count(Application.id).label("count"))
        .group_by(Application.api_type)
    )
    api_breakdown = {str(row.api_type): row.count for row in api_stats}

    # Applications by coverage target
    meeting_target = await db.scalar(
        select(func.count(Application.id)).where(Application.coverage_score >= 95.0)
    )

    # Recent test runs
    recent_runs_result = await db.execute(
        select(TestRun).order_by(TestRun.created_at.desc()).limit(10)
    )
    recent_runs = recent_runs_result.scalars().all()

    logger.info("dashboard_generated", total_apps=total_apps)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "applications": {
            "total_scanned": total_apps or 0,
            "total_tested": tested_apps or 0,
            "meeting_coverage_target": meeting_target or 0,
        },
        "tests": {
            "total_executed": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": round(avg_pass_rate, 2),
        },
        "coverage": {
            "average_overall": round(avg_coverage, 2),
            "target": 95.0,
        },
        "scores": {
            "production_readiness": round(float(score_row.readiness or 0), 1),
            "security": round(float(score_row.security or 0), 1),
            "performance": round(float(score_row.performance or 0), 1),
            "risk": round(float(score_row.risk or 0), 1),
            "coverage": round(float(score_row.coverage or 0), 1),
        },
        "failures": {
            "by_severity": failure_breakdown,
        },
        "breakdown": {
            "by_api_type": api_breakdown,
        },
        "recent_runs": [
            {
                "id": str(r.id),
                "run_number": r.run_number,
                "status": r.status.value,
                "total": r.total_tests,
                "passed": r.passed_tests,
                "failed": r.failed_tests,
                "pass_rate": r.pass_rate,
                "created_at": r.created_at.isoformat(),
            }
            for r in recent_runs
        ],
    }


@router.get("/applications", response_model=list)
async def list_applications(
    db: DBSession,
    _user: ReadUser,
    skip: int = 0,
    limit: int = 50,
    business_unit: str | None = None,
    domain: str | None = None,
    api_type: str | None = None,
) -> list:
    """List applications with optional filtering."""
    query = select(Application).offset(skip).limit(limit)
    if business_unit:
        query = query.where(Application.business_unit == business_unit)
    if domain:
        query = query.where(Application.domain == domain)
    if api_type:
        query = query.where(Application.api_type == api_type)

    result = await db.execute(query)
    apps = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "name": a.name,
            "version": a.version,
            "mule_runtime_version": a.mule_runtime_version,
            "business_unit": a.business_unit,
            "domain": a.domain,
            "environment": a.environment,
            "api_type": a.api_type.value,
            "status": a.status.value,
            "flows_count": a.flows_count,
            "coverage_score": a.coverage_score,
            "security_score": a.security_score,
            "performance_score": a.performance_score,
            "quality_score": a.quality_score,
            "production_readiness_score": a.production_readiness_score,
            "migration_readiness_score": a.migration_readiness_score,
            "risk_score": a.risk_score,
        }
        for a in apps
    ]
