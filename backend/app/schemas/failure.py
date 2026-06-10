import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FailureReportRead(BaseModel):
    id: uuid.UUID
    test_run_id: uuid.UUID
    test_name: str
    flow_name: Optional[str]
    error_message: Optional[str]
    root_cause: Optional[str]
    suggested_fix: Optional[str]
    confidence_score: float
    severity: str
    failure_category: Optional[str]
    prevention_tips: list
    is_flaky: bool
    created_at: datetime

    class Config:
        from_attributes = True
