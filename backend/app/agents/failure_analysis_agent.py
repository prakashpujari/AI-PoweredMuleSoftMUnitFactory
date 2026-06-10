"""Agent 6 — Failure Analysis Agent: LLM-powered root cause and fix generation."""
from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph, END

from app.agents.base_agent import AgentState, BaseAgent
from app.services.ai_provider import get_ai_service
from app.utils.logging import get_logger

logger = get_logger(__name__)


class FailureAnalysisAgent(BaseAgent):
    name = "failure_analysis_agent"

    def _build_graph(self) -> Any:
        graph = StateGraph(AgentState)
        graph.add_node("extract_failures", self._extract_failures)
        graph.add_node("analyze_with_llm", self._analyze_with_llm)
        graph.add_node("detect_flakiness", self._detect_flakiness)
        graph.add_node("generate_fix_suggestions", self._generate_fix_suggestions)
        graph.add_node("categorize_failures", self._categorize_failures)

        graph.set_entry_point("extract_failures")
        graph.add_edge("extract_failures", "analyze_with_llm")
        graph.add_edge("analyze_with_llm", "detect_flakiness")
        graph.add_edge("detect_flakiness", "generate_fix_suggestions")
        graph.add_edge("generate_fix_suggestions", "categorize_failures")
        graph.add_edge("categorize_failures", END)

        return graph.compile()

    async def _extract_failures(self, state: AgentState) -> AgentState:
        state["current_step"] = "extract_failures"
        surefire = state.get("surefire_results", {})
        raw_failures: list[dict] = []

        for suite in surefire.get("test_suites", []):
            # In real surefire XML, failures are nested; here we parse summary
            if suite.get("failures", 0) > 0 or suite.get("errors", 0) > 0:
                raw_failures.append({
                    "suite_name": suite.get("name", ""),
                    "test_name": suite.get("name", ""),
                    "error_message": "Test failure detected in suite",
                    "stack_trace": "",
                    "flow_xml": "",
                    "munit_xml": "",
                })

        state["raw_failures"] = raw_failures
        logger.info("failures_extracted", count=len(raw_failures))
        return state

    async def _analyze_with_llm(self, state: AgentState) -> AgentState:
        state["current_step"] = "analyze_with_llm"
        raw_failures = state.get("raw_failures", [])
        ai_service = get_ai_service()
        analyses: list[dict] = []

        for failure in raw_failures[:50]:  # Cap at 50 to manage API costs
            try:
                analysis = await ai_service.analyze_failure(
                    test_name=failure.get("test_name", ""),
                    error_message=failure.get("error_message", ""),
                    stack_trace=failure.get("stack_trace", ""),
                    flow_xml=failure.get("flow_xml", ""),
                    munit_xml=failure.get("munit_xml", ""),
                )
                analysis["test_name"] = failure.get("test_name", "")
                analysis["suite_name"] = failure.get("suite_name", "")
                analyses.append(analysis)
            except Exception as e:
                logger.warning("llm_analysis_error", test=failure.get("test_name"), error=str(e))
                analyses.append({
                    "test_name": failure.get("test_name", ""),
                    "root_cause": f"Analysis failed: {e}",
                    "suggested_fix": "Manual investigation required",
                    "confidence_score": 0.0,
                    "severity": "medium",
                })

        state["failure_analyses"] = analyses
        logger.info("llm_analyses_complete", count=len(analyses))
        return state

    async def _detect_flakiness(self, state: AgentState) -> AgentState:
        state["current_step"] = "detect_flakiness"
        analyses = state.get("failure_analyses", [])

        # Simple heuristic: if error mentions timing, race condition, or connection → flaky
        flaky_keywords = {"timeout", "connection", "race", "intermittent", "network", "retry"}

        for analysis in analyses:
            error_lower = str(analysis.get("root_cause", "")).lower()
            is_flaky = any(kw in error_lower for kw in flaky_keywords)
            analysis["is_flaky"] = analysis.get("is_flaky", is_flaky)

        state["failure_analyses"] = analyses
        return state

    async def _generate_fix_suggestions(self, state: AgentState) -> AgentState:
        state["current_step"] = "generate_fix_suggestions"
        # Analyses already contain fix suggestions from LLM — add priority ordering
        analyses = state.get("failure_analyses", [])

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        analyses.sort(key=lambda x: severity_order.get(x.get("severity", "medium"), 2))

        state["failure_analyses"] = analyses
        return state

    async def _categorize_failures(self, state: AgentState) -> AgentState:
        state["current_step"] = "categorize_failures"
        analyses = state.get("failure_analyses", [])

        categories: dict[str, int] = {}
        for analysis in analyses:
            cat = analysis.get("failure_category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        state["failure_categories"] = categories
        state["failure_summary"] = {
            "total_failures": len(analyses),
            "critical": sum(1 for a in analyses if a.get("severity") == "critical"),
            "high": sum(1 for a in analyses if a.get("severity") == "high"),
            "medium": sum(1 for a in analyses if a.get("severity") == "medium"),
            "low": sum(1 for a in analyses if a.get("severity") == "low"),
            "flaky": sum(1 for a in analyses if a.get("is_flaky")),
            "avg_confidence": (
                sum(a.get("confidence_score", 0) for a in analyses) / len(analyses)
                if analyses else 0.0
            ),
            "categories": categories,
        }

        logger.info("failures_categorized", summary=state["failure_summary"])
        return state
