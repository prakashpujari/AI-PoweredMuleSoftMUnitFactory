"""Base LangGraph agent with shared state schema and graph utilities."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from app.utils.logging import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict, total=False):
    """Shared state bag passed between agent nodes."""
    # Input
    application_id: str
    repo_path: str
    config: dict

    # Discovery outputs
    pom_metadata: dict
    flows: list[dict]
    raml_spec: dict
    app_metadata: dict

    # Analysis outputs
    flow_docs: dict
    complexity_map: dict

    # Generation outputs
    test_cases: list[dict]
    munit_files: dict

    # Execution outputs
    test_run_id: str
    surefire_results: dict
    munit_results: dict

    # Coverage outputs
    coverage_report: dict

    # Failure outputs
    failure_analyses: list[dict]
    failure_summary: dict
    failure_categories: dict
    raw_failures: list[dict]

    # Execution internals
    execution_summary: dict
    maven_output: str
    maven_stderr: str
    maven_return_code: int

    # Migration internals
    migration_report: dict
    migration_context: dict

    # Reporting outputs
    aggregated_metrics: dict
    scores: dict
    executive_summary: str
    dashboard_data: dict
    pdf_report_path: str

    # Control
    errors: list[str]
    status: str
    current_step: str


class BaseAgent(ABC):
    """Abstract base for all AI-MUnit-Factory LangGraph agents."""

    name: str = "base_agent"

    def __init__(self) -> None:
        self.logger = get_logger(f"agent.{self.name}")
        self._graph = self._build_graph()

    @abstractmethod
    def _build_graph(self) -> Any:
        """Construct and compile the LangGraph StateGraph."""

    async def run(self, initial_state: dict[str, Any]) -> AgentState:
        """Execute the agent graph with the provided initial state."""
        self.logger.info("agent_start", agent=self.name, state_keys=list(initial_state.keys()))
        state = AgentState(**initial_state)
        state.setdefault("errors", [])
        state.setdefault("status", "running")

        try:
            result = await self._graph.ainvoke(state)
            result["status"] = "completed"
            self.logger.info("agent_complete", agent=self.name)
            return result
        except Exception as e:
            self.logger.error("agent_error", agent=self.name, error=str(e))
            state["errors"].append(str(e))
            state["status"] = "failed"
            return state

    def _record_error(self, state: AgentState, error: str) -> AgentState:
        state.setdefault("errors", [])
        state["errors"].append(f"[{self.name}] {error}")
        self.logger.error("agent_step_error", agent=self.name, error=error)
        return state
