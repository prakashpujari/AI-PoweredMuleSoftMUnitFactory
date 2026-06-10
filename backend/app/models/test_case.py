"""MUnit test case model."""
import uuid
from enum import Enum as PyEnum

from sqlalchemy import String, Text, JSON, Float, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TestType(str, PyEnum):
    HAPPY_PATH = "happy_path"
    NEGATIVE_PATH = "negative_path"
    MISSING_PAYLOAD = "missing_payload"
    NULL_VALUES = "null_values"
    INVALID_DATATYPE = "invalid_datatype"
    VALIDATION_FAILURE = "validation_failure"
    DATABASE_FAILURE = "database_failure"
    SALESFORCE_FAILURE = "salesforce_failure"
    KAFKA_FAILURE = "kafka_failure"
    JMS_FAILURE = "jms_failure"
    TIMEOUT = "timeout"
    RETRY = "retry"
    OAUTH_FAILURE = "oauth_failure"
    JWT_FAILURE = "jwt_failure"
    CLIENT_ID_FAILURE = "client_id_failure"
    RATE_LIMIT = "rate_limit"
    LARGE_PAYLOAD = "large_payload"
    CONCURRENT_REQUESTS = "concurrent_requests"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR_HANDLING = "error_handling"
    BATCH = "batch"
    SCHEDULER = "scheduler"


class TestStatus(str, PyEnum):
    GENERATED = "generated"
    VALIDATED = "validated"
    EXECUTED = "executed"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    flow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flows.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    test_type: Mapped[TestType] = mapped_column(Enum(TestType), nullable=False)
    status: Mapped[TestStatus] = mapped_column(
        Enum(TestStatus), default=TestStatus.GENERATED
    )

    # Generated content
    munit_xml: Mapped[str] = mapped_column(Text, nullable=True)
    mock_config: Mapped[dict] = mapped_column(JSON, default=dict)
    assertions: Mapped[list] = mapped_column(JSON, default=list)
    test_data: Mapped[dict] = mapped_column(JSON, default=dict)

    # Execution results
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    stack_trace: Mapped[str] = mapped_column(Text, nullable=True)

    # AI metadata
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    ai_model_used: Mapped[str] = mapped_column(String(100), nullable=True)
    generation_prompt: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="test_cases")
    flow: Mapped["Flow"] = relationship("Flow", back_populates="test_cases")

    def __repr__(self) -> str:
        return f"<TestCase {self.name} [{self.test_type}]>"
