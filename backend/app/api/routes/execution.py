"""POST /execute-tests — run mvn test and collect results."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func

from app.agents.execution_agent import ExecutionAgent
from app.api.deps import DBSession, ExecuteUser
from app.models.application import Application
from app.models.test_run import TestRun, RunStatus
from app.schemas.requests import ExecuteTestsRequest
from app.utils.logging import get_logger

router = APIRouter(prefix="/execute-tests", tags=["execution"])
logger = get_logger(__name__)


@router.post("", response_model=dict)
async def execute_tests(
    request: ExecuteTestsRequest,
    db: DBSession,
    _user: ExecuteUser,
) -> dict:
    """Execute MUnit tests via Maven and return execution summary."""
    app_id = uuid.UUID(request.application_id)

    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail=f"Application {app_id} not found")

    if not app.repo_path:
        raise HTTPException(status_code=422, detail="Application has no repo_path configured")

    # Determine run number
    count_result = await db.execute(
        select(func.count(TestRun.id)).where(TestRun.application_id == app_id)
    )
    run_number = (count_result.scalar() or 0) + 1

    # Create pending run record
    test_run = TestRun(
        application_id=app_id,
        run_number=run_number,
        status=RunStatus.RUNNING,
        triggered_by=request.triggered_by,
        environment=request.environment,
    )
    db.add(test_run)
    await db.flush()

    # Execute via agent
    agent = ExecutionAgent()
    state = await agent.run({
        "repo_path": app.repo_path,
        "config": {"maven_command": request.maven_command},
    })

    # Update run record
    summary = state.get("execution_summary", {})
    surefire = state.get("surefire_results", {})

    test_run.status = RunStatus.COMPLETED if not state.get("errors") else RunStatus.FAILED
    test_run.total_tests = summary.get("total_tests", 0)
    test_run.passed_tests = summary.get("passed", 0)
    test_run.failed_tests = summary.get("failed", 0)
    test_run.skipped_tests = summary.get("skipped", 0)
    test_run.pass_rate = summary.get("pass_rate", 0.0)
    test_run.surefire_report = surefire
    test_run.maven_output = state.get("maven_output", "")[:50000]

    await db.commit()

    logger.info(
        "execution_complete",
        app=app.name,
        run=run_number,
        total=test_run.total_tests,
        passed=test_run.passed_tests,
        failed=test_run.failed_tests,
    )

    return {
        "test_run_id": str(test_run.id),
        "run_number": run_number,
        "status": test_run.status.value,
        "total_tests": test_run.total_tests,
        "passed": test_run.passed_tests,
        "failed": test_run.failed_tests,
        "skipped": test_run.skipped_tests,
        "pass_rate": test_run.pass_rate,
        "errors": state.get("errors", []),
    }
