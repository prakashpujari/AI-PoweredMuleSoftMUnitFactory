"""Inbound request schemas for all API endpoints."""
from typing import Any, Optional
from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    repo_path: str = Field(..., min_length=1, description="Absolute path to the MuleSoft project root")
    business_unit: Optional[str] = None
    domain: Optional[str] = None
    environment: Optional[str] = "development"
    api_type: Optional[str] = "unknown"
    ai_provider: Optional[str] = "groq"


class GenerateMUnitRequest(BaseModel):
    application_id: str
    test_types: Optional[list[str]] = None
    target_coverage: Optional[float] = 95.0
    ai_provider: Optional[str] = "groq"
    overwrite_existing: Optional[bool] = False


class ExecuteTestsRequest(BaseModel):
    application_id: str
    environment: Optional[str] = "test"
    maven_command: Optional[str] = "mvn clean test -B"
    triggered_by: Optional[str] = "api"


class CoverageAnalysisRequest(BaseModel):
    application_id: str
    test_run_id: Optional[str] = None


class FailureAnalysisRequest(BaseModel):
    test_run_id: str
    ai_provider: Optional[str] = "groq"


class MigrationAnalysisRequest(BaseModel):
    application_id: str
    source_version: Optional[str] = None
    target_version: str = "4.9.0"
    ai_provider: Optional[str] = "groq"


class BulkScanRequest(BaseModel):
    repo_paths: list[str]
    business_unit: Optional[str] = None
    ai_provider: Optional[str] = "groq"
