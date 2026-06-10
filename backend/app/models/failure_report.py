"""AI-powered failure analysis report model."""
import uuid
from enum import Enum as PyEnum

from sqlalchemy import String, Text, Float, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FailureSeverity(str, PyEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FailureReport(Base):
    __tablename__ = "failure_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    test_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    test_name: Mapped[str] = mapped_column(String(500), nullable=False)
    flow_name: Mapped[str] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    stack_trace: Mapped[str] = mapped_column(Text, nullable=True)

    # AI Analysis
    root_cause: Mapped[str] = mapped_column(Text, nullable=True)
    suggested_fix: Mapped[str] = mapped_column(Text, nullable=True)
    fix_code_snippet: Mapped[str] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[FailureSeverity] = mapped_column(
        Enum(FailureSeverity), default=FailureSeverity.MEDIUM
    )
    failure_category: Mapped[str] = mapped_column(String(100), nullable=True)
    similar_failures: Mapped[list] = mapped_column(JSON, default=list)
    prevention_tips: Mapped[list] = mapped_column(JSON, default=list)
    is_flaky: Mapped[bool] = mapped_column(default=False)
    recurrence_count: Mapped[int] = mapped_column(default=1)

    # Relationships
    test_run: Mapped["TestRun"] = relationship("TestRun", back_populates="failure_reports")

    def __repr__(self) -> str:
        return f"<FailureReport {self.test_name} [{self.severity}]>"
