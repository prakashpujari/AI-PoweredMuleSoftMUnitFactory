"""POST /analyze-failures — AI root cause analysis of test failures."""
import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.agents.failure_analysis_agent import FailureAnalysisAgent
from app.api.deps import DBSession, ReadUser
from app.models.failure_report import FailureReport, FailureSeverity
from app.models.test_run import TestRun
from app.schemas.requests import FailureAnalysisRequest
from app.utils.logging import get_logger

router = APIRouter(prefix="/analyze-failures", tags=["failures"])
logger = get_logger(__name__)


@router.post("", response_model=dict)
async def analyze_failures(
    request: FailureAnalysisRequest,
    db: DBSession,
    _user: ReadUser,
) -> dict:
    """Run AI failure analysis on a test run's failed tests."""
    run_id = uuid.UUID(request.test_run_id)

    result = await db.execute(select(TestRun).where(TestRun.id == run_id))
    test_run = result.scalar_one_or_none()
    if not test_run:
        raise HTTPException(status_code=404, detail=f"TestRun {run_id} not found")

    surefire = test_run.surefire_report or {}
    state = {
        "surefire_results": surefire,
        "config": {"ai_provider": request.ai_provider},
    }

    agent = FailureAnalysisAgent()
    state = await agent.run(state)

    analyses = state.get("failure_analyses", [])

    # Persist failure reports
    persisted = []
    for analysis in analyses:
        severity_str = analysis.get("severity", "medium")
        try:
            severity = FailureSeverity(severity_str)
        except ValueError:
            severity = FailureSeverity.MEDIUM

        report = FailureReport(
            test_run_id=run_id,
            application_id=test_run.application_id,
            test_name=analysis.get("test_name", ""),
            flow_name=analysis.get("suite_name", ""),
            error_message="",
            root_cause=analysis.get("root_cause", ""),
            suggested_fix=analysis.get("suggested_fix", ""),
            fix_code_snippet=analysis.get("fix_code_snippet", ""),
            confidence_score=float(analysis.get("confidence_score", 0)),
            severity=severity,
            failure_category=analysis.get("failure_category", "unknown"),
            prevention_tips=analysis.get("prevention_tips", []),
            is_flaky=bool(analysis.get("is_flaky", False)),
        )
        db.add(report)
        persisted.append({
            "test_name": report.test_name,
            "severity": report.severity.value,
            "root_cause": report.root_cause[:200] if report.root_cause else "",
            "confidence": report.confidence_score,
        })

    await db.commit()

    return {
        "test_run_id": str(run_id),
        "analyses_count": len(analyses),
        "summary": state.get("failure_summary", {}),
        "analyses": persisted,
        "errors": state.get("errors", []),
    }
