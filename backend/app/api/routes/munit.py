"""POST /generate-munit — AI-generate MUnit test suites."""
import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.agents.munit_generation_agent import MUnitGenerationAgent
from app.agents.coverage_agent import CoverageAgent
from app.api.deps import DBSession, WriteUser
from app.models.application import Application, ApplicationStatus
from app.models.flow import Flow
from app.models.test_case import TestCase, TestType, TestStatus
from app.schemas.requests import GenerateMUnitRequest
from app.utils.logging import get_logger

router = APIRouter(prefix="/generate-munit", tags=["munit"])
logger = get_logger(__name__)


@router.post("", response_model=dict)
async def generate_munit(
    request: GenerateMUnitRequest,
    db: DBSession,
    _user: WriteUser,
) -> dict:
    """Generate AI-powered MUnit test suites for a scanned application."""
    app_id = uuid.UUID(request.application_id)

    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail=f"Application {app_id} not found")

    # Load flows
    flows_result = await db.execute(select(Flow).where(Flow.application_id == app_id))
    flows = flows_result.scalars().all()
    if not flows:
        raise HTTPException(status_code=422, detail="No flows found. Run /scan first.")

    # Build state for agent
    state = {
        "repo_path": app.repo_path or "",
        "flows": [
            {
                "name": f.name,
                "flow_type": f.flow_type.value,
                "connectors_used": f.connectors_used or [],
                "raw_xml": f.raw_xml or "",
                "has_dataweave": f.has_dataweave,
                "has_error_handler": f.has_error_handler,
                "processor_count": f.processor_count,
                "processors": f.processors or [],
            }
            for f in flows
        ],
        "raml_spec": {},
        "app_metadata": {"name": app.name},
        "config": {
            "ai_provider": request.ai_provider or "groq",
            "target_coverage": request.target_coverage or 95.0,
        },
    }

    # Generate tests
    gen_agent = MUnitGenerationAgent()
    state = await gen_agent.run(state)

    if state.get("status") == "failed":
        raise HTTPException(status_code=500, detail=state.get("errors", ["Generation failed"]))

    # Compute coverage
    cov_agent = CoverageAgent()
    state = await cov_agent.run(state)

    # Persist test cases
    test_cases = state.get("test_cases", [])
    persisted = 0

    for tc in test_cases:
        for test_type_str in tc.get("test_types", ["happy_path"]):
            try:
                tt = TestType(test_type_str)
            except ValueError:
                tt = TestType.HAPPY_PATH

            flow = next((f for f in flows if f.name == tc["flow_name"]), None)
            test_case = TestCase(
                application_id=app_id,
                flow_id=flow.id if flow else None,
                name=f"{tc['flow_name']} - {test_type_str}",
                test_type=tt,
                status=TestStatus.GENERATED,
                munit_xml=tc.get("munit_xml", ""),
                confidence_score=tc.get("confidence_score", 0.0),
                ai_generated=True,
                ai_model_used=tc.get("ai_model", "groq"),
            )
            db.add(test_case)
            persisted += 1

    # Update application scores
    coverage_report = state.get("coverage_report", {})
    app.coverage_score = coverage_report.get("overall_coverage", 0.0)
    app.status = ApplicationStatus.TESTED

    await db.commit()

    logger.info(
        "munit_generated",
        app=app.name,
        tests=persisted,
        coverage=coverage_report.get("overall_coverage"),
    )

    return {
        "application_id": str(app_id),
        "flows_processed": len(flows),
        "test_cases_generated": persisted,
        "total_munit_tests": sum(tc.get("test_count", 0) for tc in test_cases),
        "coverage": coverage_report,
        "munit_files": state.get("munit_files", {}),
        "errors": state.get("errors", []),
    }
