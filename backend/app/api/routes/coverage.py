"""POST /coverage — analyze and store coverage metrics."""
import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.agents.coverage_agent import CoverageAgent
from app.api.deps import DBSession, ReadUser
from app.models.application import Application
from app.models.coverage_report import CoverageReport
from app.models.flow import Flow
from app.models.test_case import TestCase
from app.schemas.requests import CoverageAnalysisRequest
from app.utils.logging import get_logger

router = APIRouter(prefix="/coverage", tags=["coverage"])
logger = get_logger(__name__)


@router.post("", response_model=dict)
async def analyze_coverage(
    request: CoverageAnalysisRequest,
    db: DBSession,
    _user: ReadUser,
) -> dict:
    """Compute coverage metrics for an application's test suite."""
    app_id = uuid.UUID(request.application_id)

    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail=f"Application {app_id} not found")

    flows_result = await db.execute(select(Flow).where(Flow.application_id == app_id))
    flows = flows_result.scalars().all()

    tests_result = await db.execute(select(TestCase).where(TestCase.application_id == app_id))
    test_cases = tests_result.scalars().all()

    state = {
        "flows": [
            {
                "name": f.name,
                "flow_type": f.flow_type.value,
                "processor_count": f.processor_count,
                "has_error_handler": f.has_error_handler,
            }
            for f in flows
        ],
        "test_cases": [
            {
                "flow_name": tc.name.split(" - ")[0] if " - " in tc.name else tc.name,
                "test_types": [tc.test_type.value],
            }
            for tc in test_cases
        ],
        "config": {},
    }

    agent = CoverageAgent()
    state = await agent.run(state)
    report_data = state.get("coverage_report", {})

    # Persist coverage report
    coverage_report = CoverageReport(
        application_id=app_id,
        test_run_id=uuid.UUID(request.test_run_id) if request.test_run_id else None,
        flow_coverage=report_data.get("flow_coverage", 0.0),
        processor_coverage=report_data.get("processor_coverage", 0.0),
        error_handler_coverage=report_data.get("error_handler_coverage", 0.0),
        overall_coverage=report_data.get("overall_coverage", 0.0),
        total_flows=report_data.get("total_flows", 0),
        covered_flows=report_data.get("covered_flows", 0),
        total_processors=report_data.get("total_processors", 0),
        covered_processors=report_data.get("covered_processors", 0),
        uncovered_flows=report_data.get("uncovered_flows", []),
        coverage_gaps=report_data.get("coverage_gaps", []),
        ai_recommendations=report_data.get("ai_recommendations"),
        meets_target=report_data.get("meets_target", False),
    )
    db.add(coverage_report)

    # Update application coverage score
    app.coverage_score = report_data.get("overall_coverage", 0.0)
    await db.commit()

    return {
        "coverage_report_id": str(coverage_report.id),
        "application_id": str(app_id),
        **report_data,
    }


@router.get("/{application_id}", response_model=dict)
async def get_latest_coverage(
    application_id: str,
    db: DBSession,
    _user: ReadUser,
) -> dict:
    """Retrieve latest coverage report for an application."""
    app_id = uuid.UUID(application_id)
    result = await db.execute(
        select(CoverageReport)
        .where(CoverageReport.application_id == app_id)
        .order_by(CoverageReport.created_at.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="No coverage report found")

    return {
        "coverage_report_id": str(report.id),
        "flow_coverage": report.flow_coverage,
        "processor_coverage": report.processor_coverage,
        "error_handler_coverage": report.error_handler_coverage,
        "overall_coverage": report.overall_coverage,
        "meets_target": report.meets_target,
        "uncovered_flows": report.uncovered_flows,
        "coverage_gaps": report.coverage_gaps,
        "ai_recommendations": report.ai_recommendations,
    }
