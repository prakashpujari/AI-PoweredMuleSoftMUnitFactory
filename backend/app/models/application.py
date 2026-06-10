"""SQLAlchemy model for a MuleSoft application."""
import uuid
from enum import Enum as PyEnum

from sqlalchemy import String, Float, Integer, JSON, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ApiType(str, PyEnum):
    SYSTEM = "system"
    PROCESS = "process"
    EXPERIENCE = "experience"
    UNKNOWN = "unknown"


class DeploymentTarget(str, PyEnum):
    CLOUDHUB = "cloudhub"
    RUNTIME_FABRIC = "runtime_fabric"
    HYBRID = "hybrid"
    ON_PREMISE = "on_premise"


class ApplicationStatus(str, PyEnum):
    DISCOVERED = "discovered"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    GENERATING = "generating"
    TESTED = "tested"
    FAILED = "failed"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    group_id: Mapped[str] = mapped_column(String(255), nullable=True)
    artifact_id: Mapped[str] = mapped_column(String(255), nullable=True)
    version: Mapped[str] = mapped_column(String(50), nullable=True)
    mule_runtime_version: Mapped[str] = mapped_column(String(50), nullable=True)
    repo_url: Mapped[str] = mapped_column(String(500), nullable=True)
    repo_path: Mapped[str] = mapped_column(String(500), nullable=True)
    business_unit: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    environment: Mapped[str] = mapped_column(String(100), nullable=True, index=True)

    api_type: Mapped[ApiType] = mapped_column(
        Enum(ApiType), default=ApiType.UNKNOWN, nullable=False
    )
    deployment_target: Mapped[DeploymentTarget] = mapped_column(
        Enum(DeploymentTarget), default=DeploymentTarget.CLOUDHUB, nullable=False
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.DISCOVERED, nullable=False
    )

    # Parsed metadata
    flows_count: Mapped[int] = mapped_column(Integer, default=0)
    connectors: Mapped[list] = mapped_column(JSON, default=list)
    dependencies: Mapped[dict] = mapped_column(JSON, default=dict)
    raml_spec: Mapped[str] = mapped_column(Text, nullable=True)
    pom_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # Scores
    coverage_score: Mapped[float] = mapped_column(Float, default=0.0)
    security_score: Mapped[float] = mapped_column(Float, default=0.0)
    performance_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    production_readiness_score: Mapped[float] = mapped_column(Float, default=0.0)
    migration_readiness_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    flows: Mapped[list["Flow"]] = relationship(
        "Flow", back_populates="application", cascade="all, delete-orphan"
    )
    test_cases: Mapped[list["TestCase"]] = relationship(
        "TestCase", back_populates="application", cascade="all, delete-orphan"
    )
    test_runs: Mapped[list["TestRun"]] = relationship(
        "TestRun", back_populates="application", cascade="all, delete-orphan"
    )
    coverage_reports: Mapped[list["CoverageReport"]] = relationship(
        "CoverageReport", back_populates="application", cascade="all, delete-orphan"
    )
    migration_reports: Mapped[list["MigrationReport"]] = relationship(
        "MigrationReport", back_populates="application", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Application {self.name} v{self.version}>"
