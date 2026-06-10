import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CoverageReportRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    flow_coverage: float
    processor_coverage: float
    error_handler_coverage: float
    overall_coverage: float
    total_flows: int
    covered_flows: int
    total_processors: int
    covered_processors: int
    uncovered_flows: list
    coverage_gaps: list
    ai_recommendations: Optional[str]
    meets_target: bool
    created_at: datetime

    class Config:
        from_attributes = True
