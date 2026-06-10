"""Migration assessment report model."""
import uuid
from enum import Enum as PyEnum

from sqlalchemy import String, Text, Float, JSON, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RiskLevel(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MigrationReport(Base):
    __tablename__ = "migration_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_version: Mapped[str] = mapped_column(String(50), nullable=False)
    target_version: Mapped[str] = mapped_column(String(50), nullable=False)
    overall_risk: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel), default=RiskLevel.MEDIUM
    )

    # Risk breakdown
    connector_risks: Mapped[list] = mapped_column(JSON, default=list)
    java_version_risks: Mapped[list] = mapped_column(JSON, default=list)
    policy_risks: Mapped[list] = mapped_column(JSON, default=list)
    dependency_risks: Mapped[list] = mapped_column(JSON, default=list)
    breaking_changes: Mapped[list] = mapped_column(JSON, default=list)

    # Scores
    migration_readiness_score: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_effort_days: Mapped[int] = mapped_column(Integer, default=0)
    risk_count_critical: Mapped[int] = mapped_column(Integer, default=0)
    risk_count_high: Mapped[int] = mapped_column(Integer, default=0)
    risk_count_medium: Mapped[int] = mapped_column(Integer, default=0)
    risk_count_low: Mapped[int] = mapped_column(Integer, default=0)

    # AI-generated guidance
    migration_plan: Mapped[str] = mapped_column(Text, nullable=True)
    recommended_approach: Mapped[str] = mapped_column(Text, nullable=True)
    required_testing: Mapped[list] = mapped_column(JSON, default=list)
    rollback_strategy: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="migration_reports")

    def __repr__(self) -> str:
        return f"<MigrationReport {self.source_version}→{self.target_version} [{self.overall_risk}]>"
