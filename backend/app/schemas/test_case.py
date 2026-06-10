import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class TestCaseCreate(BaseModel):
    application_id: uuid.UUID
    flow_id: Optional[uuid.UUID] = None
    name: str
    test_type: str
    munit_xml: Optional[str] = None
    confidence_score: float = 0.0


class TestCaseRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    name: str
    test_type: str
    status: str
    munit_xml: Optional[str]
    confidence_score: float
    ai_generated: bool
    created_at: datetime

    class Config:
        from_attributes = True
