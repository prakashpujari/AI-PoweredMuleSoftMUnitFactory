"""POST /scan — discover and inventory a MuleSoft application."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import select

from app.agents.discovery_agent import DiscoveryAgent
from app.agents.flow_analysis_agent import FlowAnalysisAgent
from app.api.deps import DBSession, WriteUser
from app.models.application import Application, ApplicationStatus, ApiType, DeploymentTarget
from app.models.flow import Flow, FlowType
from app.schemas.requests import ScanRequest, BulkScanRequest
from app.schemas.application import ApplicationRead
from app.utils.logging import get_logger

router = APIRouter(prefix="/scan", tags=["scan"])
logger = get_logger(__name__)


@router.post("", response_model=dict)
async def scan_application(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: DBSession,
    _user: WriteUser,
) -> dict:
    """Discover a MuleSoft application, parse pom.xml/Mule XML/RAML, persist inventory."""
    logger.info("scan_requested", path=request.repo_path)

    # Run discovery agent
    discovery = DiscoveryAgent()
    analysis = FlowAnalysisAgent()

    state = await discovery.run({
        "repo_path": request.repo_path,
        "config": {"ai_provider": request.ai_provider},
    })

    if state.get("status") == "failed":
        raise HTTPException(status_code=422, detail=state.get("errors", ["Unknown error"]))

    state = await analysis.run(state)

    meta = state.get("app_metadata", {})
    pom = state.get("pom_metadata", {})

    # Persist Application
    app = Application(
        name=meta.get("name", "unknown"),
        group_id=pom.get("group_id"),
        artifact_id=pom.get("artifact_id"),
        version=pom.get("version"),
        mule_runtime_version=meta.get("mule_runtime_version"),
        repo_path=request.repo_path,
        business_unit=request.business_unit,
        domain=request.domain,
        environment=request.environment,
        api_type=ApiType(request.api_type) if request.api_type else ApiType.UNKNOWN,
        deployment_target=DeploymentTarget.CLOUDHUB,
        status=ApplicationStatus.ANALYZED,
        flows_count=len(state.get("flows", [])),
        connectors=meta.get("connectors", []),
        dependencies=pom,
        pom_metadata=pom,
    )
    db.add(app)
    await db.flush()

    # Persist Flows
    for flow_dict in state.get("flows", []):
        flow_type_str = flow_dict.get("flow_type", "flow")
        try:
            flow_type = FlowType(flow_type_str)
        except ValueError:
            flow_type = FlowType.FLOW

        flow = Flow(
            application_id=app.id,
            name=flow_dict.get("name", ""),
            flow_type=flow_type,
            source_file=flow_dict.get("source_file", ""),
            processors=flow_dict.get("processors", []),
            connectors_used=flow_dict.get("connectors_used", []),
            error_handlers=flow_dict.get("error_handlers", []),
            dataweave_scripts=flow_dict.get("dataweave_scripts", []),
            processor_count=flow_dict.get("processor_count", 0),
            has_error_handler=flow_dict.get("has_error_handler", False),
            has_dataweave=flow_dict.get("has_dataweave", False),
            raw_xml=flow_dict.get("raw_xml", ""),
            ai_documentation=state.get("flow_docs", {}).get(flow_dict.get("name", ""), ""),
            complexity_score=state.get("complexity_map", {}).get(flow_dict.get("name", ""), 1),
        )
        db.add(flow)

    await db.commit()
    logger.info("application_persisted", app_id=str(app.id), name=app.name)

    return {
        "application_id": str(app.id),
        "name": app.name,
        "flows_count": app.flows_count,
        "connectors": app.connectors,
        "mule_runtime_version": app.mule_runtime_version,
        "status": app.status.value,
        "errors": state.get("errors", []),
    }


@router.post("/bulk", response_model=dict)
async def bulk_scan(
    request: BulkScanRequest,
    background_tasks: BackgroundTasks,
    db: DBSession,
    _user: WriteUser,
) -> dict:
    """Kick off background scan for multiple repositories."""
    import asyncio

    async def _scan_one(path: str) -> dict:
        discovery = DiscoveryAgent()
        state = await discovery.run({
            "repo_path": path,
            "config": {"ai_provider": request.ai_provider},
        })
        return {
            "path": path,
            "name": state.get("app_metadata", {}).get("name", "unknown"),
            "flows": len(state.get("flows", [])),
            "status": state.get("status"),
            "errors": state.get("errors", []),
        }

    tasks = [_scan_one(p) for p in request.repo_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return {
        "total": len(request.repo_paths),
        "results": [
            r if isinstance(r, dict) else {"error": str(r)}
            for r in results
        ],
    }
