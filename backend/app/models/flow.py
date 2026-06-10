"""Flow and SubFlow model representing parsed Mule XML artifacts."""
import uuid
from enum import Enum as PyEnum

from sqlalchemy import String, Text, JSON, Integer, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FlowType(str, PyEnum):
    FLOW = "flow"
    SUBFLOW = "subflow"
    ERROR_HANDLER = "error_handler"
    BATCH_JOB = "batch_job"
    SCHEDULER = "scheduler"


class Flow(Base):
    __tablename__ = "flows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    flow_type: Mapped[FlowType] = mapped_column(
        Enum(FlowType), default=FlowType.FLOW, nullable=False
    )
    source_file: Mapped[str] = mapped_column(String(500), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Parsed structure
    processors: Mapped[list] = mapped_column(JSON, default=list)
    connectors_used: Mapped[list] = mapped_column(JSON, default=list)
    error_handlers: Mapped[list] = mapped_column(JSON, default=list)
    dataweave_scripts: Mapped[list] = mapped_column(JSON, default=list)
    variables: Mapped[dict] = mapped_column(JSON, default=dict)

    # Metadata
    processor_count: Mapped[int] = mapped_column(Integer, default=0)
    has_error_handler: Mapped[bool] = mapped_column(Boolean, default=False)
    has_dataweave: Mapped[bool] = mapped_column(Boolean, default=False)
    is_async: Mapped[bool] = mapped_column(Boolean, default=False)
    is_covered: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_xml: Mapped[str] = mapped_column(Text, nullable=True)

    # AI-generated docs
    ai_documentation: Mapped[str] = mapped_column(Text, nullable=True)
    complexity_score: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="flows")
    test_cases: Mapped[list["TestCase"]] = relationship(
        "TestCase", back_populates="flow", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Flow {self.name} ({self.flow_type})>"
