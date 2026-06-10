"""Test execution run model."""
import uuid
from enum import Enum as PyEnum

from sqlalchemy import String, Text, JSON, Float, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RunStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus), default=RunStatus.PENDING, nullable=False
    )
    triggered_by: Mapped[str] = mapped_column(String(255), nullable=True)
    environment: Mapped[str] = mapped_column(String(100), nullable=True)
    branch: Mapped[str] = mapped_column(String(255), nullable=True)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=True)

    # Counts
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    passed_tests: Mapped[int] = mapped_column(Integer, default=0)
    failed_tests: Mapped[int] = mapped_column(Integer, default=0)
    skipped_tests: Mapped[int] = mapped_column(Integer, default=0)
    error_tests: Mapped[int] = mapped_column(Integer, default=0)

    # Metrics
    pass_rate: Mapped[float] = mapped_column(Float, default=0.0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)

    # Raw reports
    surefire_report: Mapped[dict] = mapped_column(JSON, default=dict)
    munit_report: Mapped[dict] = mapped_column(JSON, default=dict)
    maven_output: Mapped[str] = mapped_column(Text, nullable=True)
    error_output: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="test_runs")
    failure_reports: Mapped[list["FailureReport"]] = relationship(
        "FailureReport", back_populates="test_run", cascade="all, delete-orphan"
    )
    coverage_reports: Mapped[list["CoverageReport"]] = relationship(
        "CoverageReport", back_populates="test_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TestRun #{self.run_number} [{self.status}]>"
