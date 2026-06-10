"""Coverage report model."""
import uuid

from sqlalchemy import Float, Integer, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CoverageReport(Base):
    __tablename__ = "coverage_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    test_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Coverage percentages
    flow_coverage: Mapped[float] = mapped_column(Float, default=0.0)
    processor_coverage: Mapped[float] = mapped_column(Float, default=0.0)
    error_handler_coverage: Mapped[float] = mapped_column(Float, default=0.0)
    overall_coverage: Mapped[float] = mapped_column(Float, default=0.0)

    # Counts
    total_flows: Mapped[int] = mapped_column(Integer, default=0)
    covered_flows: Mapped[int] = mapped_column(Integer, default=0)
    total_processors: Mapped[int] = mapped_column(Integer, default=0)
    covered_processors: Mapped[int] = mapped_column(Integer, default=0)
    uncovered_flows: Mapped[list] = mapped_column(JSON, default=list)
    uncovered_processors: Mapped[list] = mapped_column(JSON, default=list)

    # Analysis
    coverage_by_type: Mapped[dict] = mapped_column(JSON, default=dict)
    coverage_gaps: Mapped[list] = mapped_column(JSON, default=list)
    ai_recommendations: Mapped[str] = mapped_column(Text, nullable=True)
    meets_target: Mapped[bool] = mapped_column(default=False)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="coverage_reports")
    test_run: Mapped["TestRun"] = relationship("TestRun", back_populates="coverage_reports")

    def __repr__(self) -> str:
        return f"<CoverageReport {self.overall_coverage:.1f}%>"
