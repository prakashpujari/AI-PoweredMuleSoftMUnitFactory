"""Application Pydantic schemas."""
import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    name: str
    group_id: Optional[str] = None
    artifact_id: Optional[str] = None
    version: Optional[str] = None
    mule_runtime_version: Optional[str] = None
    repo_url: Optional[str] = None
    repo_path: Optional[str] = None
    business_unit: Optional[str] = None
    domain: Optional[str] = None
    environment: Optional[str] = "development"
    api_type: str = "unknown"
    deployment_target: str = "cloudhub"


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    coverage_score: Optional[float] = None
    security_score: Optional[float] = None
    performance_score: Optional[float] = None
    production_readiness_score: Optional[float] = None
    migration_readiness_score: Optional[float] = None
    risk_score: Optional[float] = None


class ApplicationRead(BaseModel):
    id: uuid.UUID
    name: str
    group_id: Optional[str]
    artifact_id: Optional[str]
    version: Optional[str]
    mule_runtime_version: Optional[str]
    business_unit: Optional[str]
    domain: Optional[str]
    environment: Optional[str]
    api_type: str
    deployment_target: str
    status: str
    flows_count: int
    connectors: list
    coverage_score: float
    security_score: float
    performance_score: float
    quality_score: float
    production_readiness_score: float
    migration_readiness_score: float
    risk_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
