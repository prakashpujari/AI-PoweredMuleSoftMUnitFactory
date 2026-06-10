"""POST /migration-analysis — assess Mule version migration risks."""
import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.agents.migration_agent import MigrationAgent
from app.api.deps import DBSession, ReadUser
from app.models.application import Application
from app.models.migration_report import MigrationReport, RiskLevel
from app.schemas.requests import MigrationAnalysisRequest
from app.utils.logging import get_logger

router = APIRouter(prefix="/migration-analysis", tags=["migration"])
logger = get_logger(__name__)


@router.post("", response_model=dict)
async def migration_analysis(
    request: MigrationAnalysisRequest,
    db: DBSession,
    _user: ReadUser,
) -> dict:
    """Assess migration risk from current Mule version to target version."""
    app_id = uuid.UUID(request.application_id)

    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail=f"Application {app_id} not found")

    source_version = request.source_version or app.mule_runtime_version or "4.4.0"

    state = {
        "repo_path": app.repo_path or "",
        "pom_metadata": app.pom_metadata or {},
        "app_metadata": {
            "name": app.name,
            "connectors": app.connectors or [],
        },
        "raml_spec": {},
        "config": {
            "source_version": source_version,
            "target_version": request.target_version,
            "ai_provider": request.ai_provider,
        },
    }

    agent = MigrationAgent()
    state = await agent.run(state)

    migration_data = state.get("migration_report", {})

    # Persist migration report
    try:
        risk_level = RiskLevel(migration_data.get("overall_risk", "medium"))
    except ValueError:
        risk_level = RiskLevel.MEDIUM

    report = MigrationReport(
        application_id=app_id,
        source_version=source_version,
        target_version=request.target_version,
        overall_risk=risk_level,
        connector_risks=migration_data.get("connector_risks", []),
        java_version_risks=migration_data.get("java_version_risks", []),
        policy_risks=migration_data.get("policy_risks", []),
        dependency_risks=migration_data.get("dependency_risks", []),
        breaking_changes=migration_data.get("breaking_changes", []),
        migration_readiness_score=float(migration_data.get("migration_readiness_score", 0)),
        estimated_effort_days=int(migration_data.get("estimated_effort_days", 0)),
        migration_plan=migration_data.get("migration_plan", ""),
        recommended_approach=migration_data.get("recommended_approach", ""),
        rollback_strategy=migration_data.get("rollback_strategy", ""),
        risk_count_critical=migration_data.get("risk_count_critical", 0),
        risk_count_high=migration_data.get("risk_count_high", 0),
        risk_count_medium=migration_data.get("risk_count_medium", 0),
    )
    db.add(report)

    app.migration_readiness_score = report.migration_readiness_score
    await db.commit()

    return {
        "migration_report_id": str(report.id),
        "application_id": str(app_id),
        "application_name": app.name,
        **migration_data,
    }
