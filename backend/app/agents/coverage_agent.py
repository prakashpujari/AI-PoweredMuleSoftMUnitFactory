"""Agent 4 — Coverage Agent: analyzes flow/processor coverage, generates gap tests."""
from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph, END

from app.agents.base_agent import AgentState, BaseAgent
from app.config import get_settings
from app.services.ai_provider import get_ai_service
from app.utils.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class CoverageAgent(BaseAgent):
    name = "coverage_agent"

    def _build_graph(self) -> Any:
        graph = StateGraph(AgentState)
        graph.add_node("compute_flow_coverage", self._compute_flow_coverage)
        graph.add_node("compute_processor_coverage", self._compute_processor_coverage)
        graph.add_node("compute_error_coverage", self._compute_error_coverage)
        graph.add_node("identify_gaps", self._identify_gaps)
        graph.add_node("recommend_missing_tests", self._recommend_missing_tests)
        graph.add_node("build_coverage_report", self._build_coverage_report)

        graph.set_entry_point("compute_flow_coverage")
        graph.add_edge("compute_flow_coverage", "compute_processor_coverage")
        graph.add_edge("compute_processor_coverage", "compute_error_coverage")
        graph.add_edge("compute_error_coverage", "identify_gaps")
        graph.add_edge("identify_gaps", "recommend_missing_tests")
        graph.add_edge("recommend_missing_tests", "build_coverage_report")
        graph.add_edge("build_coverage_report", END)

        return graph.compile()

    async def _compute_flow_coverage(self, state: AgentState) -> AgentState:
        state["current_step"] = "compute_flow_coverage"
        flows = state.get("flows", [])
        test_cases = state.get("test_cases", [])

        tested_flows = {tc["flow_name"] for tc in test_cases}
        total_flows = [f["name"] for f in flows if f.get("flow_type") != "subflow"]
        covered_flows = [f for f in total_flows if f in tested_flows]
        uncovered = [f for f in total_flows if f not in tested_flows]

        coverage = (len(covered_flows) / len(total_flows) * 100) if total_flows else 0.0

        state.setdefault("coverage_report", {})
        state["coverage_report"].update({
            "total_flows": len(total_flows),
            "covered_flows": len(covered_flows),
            "uncovered_flows": uncovered,
            "flow_coverage": round(coverage, 2),
        })
        logger.info("flow_coverage", percent=coverage, covered=len(covered_flows), total=len(total_flows))
        return state

    async def _compute_processor_coverage(self, state: AgentState) -> AgentState:
        state["current_step"] = "compute_processor_coverage"
        flows = state.get("flows", [])
        test_cases = state.get("test_cases", [])

        tested_flow_names = {tc["flow_name"] for tc in test_cases}
        total_processors = sum(f.get("processor_count", 0) for f in flows)
        covered_processors = sum(
            f.get("processor_count", 0)
            for f in flows
            if f.get("name") in tested_flow_names
        )

        coverage = (covered_processors / total_processors * 100) if total_processors else 0.0

        state["coverage_report"].update({
            "total_processors": total_processors,
            "covered_processors": covered_processors,
            "processor_coverage": round(coverage, 2),
        })
        return state

    async def _compute_error_coverage(self, state: AgentState) -> AgentState:
        state["current_step"] = "compute_error_coverage"
        flows = state.get("flows", [])
        test_cases = state.get("test_cases", [])

        flows_with_handlers = [f for f in flows if f.get("has_error_handler")]
        total_handlers = len(flows_with_handlers)

        handler_tested = sum(
            1 for f in flows_with_handlers
            if any(tc["flow_name"] == f["name"] and "error_handling" in tc.get("test_types", [])
                   for tc in test_cases)
        )

        coverage = (handler_tested / total_handlers * 100) if total_handlers else 100.0

        state["coverage_report"].update({
            "total_error_handlers": total_handlers,
            "covered_error_handlers": handler_tested,
            "error_handler_coverage": round(coverage, 2),
        })
        return state

    async def _identify_gaps(self, state: AgentState) -> AgentState:
        state["current_step"] = "identify_gaps"
        report = state.get("coverage_report", {})
        uncovered = report.get("uncovered_flows", [])

        gaps = []
        for flow_name in uncovered:
            gaps.append({
                "flow": flow_name,
                "gap_type": "no_tests",
                "priority": "high",
                "recommendation": f"Generate happy_path and negative_path tests for {flow_name}",
            })

        state["coverage_report"]["coverage_gaps"] = gaps
        logger.info("gaps_identified", count=len(gaps))
        return state

    async def _recommend_missing_tests(self, state: AgentState) -> AgentState:
        state["current_step"] = "recommend_missing_tests"
        report = state.get("coverage_report", {})
        current_coverage = report.get("flow_coverage", 0.0)
        uncovered = report.get("uncovered_flows", [])

        if current_coverage >= settings.COVERAGE_TARGET_PERCENT:
            state["coverage_report"]["ai_recommendations"] = (
                f"Coverage target of {settings.COVERAGE_TARGET_PERCENT}% achieved."
            )
            return state

        try:
            ai_service = get_ai_service()
            recs = await ai_service.generate_coverage_recommendations(
                uncovered_flows=uncovered,
                uncovered_processors=report.get("uncovered_processors", []),
                current_coverage=current_coverage,
            )
            state["coverage_report"]["ai_recommendations"] = recs
        except Exception as e:
            logger.warning("coverage_recommendations_error", error=str(e))
            state["coverage_report"]["ai_recommendations"] = (
                f"Coverage at {current_coverage:.1f}%. {len(uncovered)} flows need tests."
            )

        return state

    async def _build_coverage_report(self, state: AgentState) -> AgentState:
        state["current_step"] = "build_coverage_report"
        report = state["coverage_report"]

        # Overall coverage = weighted average
        weights = {"flow": 0.5, "processor": 0.3, "error_handler": 0.2}
        overall = (
            report.get("flow_coverage", 0) * weights["flow"]
            + report.get("processor_coverage", 0) * weights["processor"]
            + report.get("error_handler_coverage", 0) * weights["error_handler"]
        )
        report["overall_coverage"] = round(overall, 2)
        report["meets_target"] = overall >= settings.COVERAGE_TARGET_PERCENT

        logger.info(
            "coverage_report_complete",
            overall=overall,
            meets_target=report["meets_target"],
        )
        state["coverage_report"] = report
        return state
