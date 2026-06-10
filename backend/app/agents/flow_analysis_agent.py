"""Agent 2 — Flow Analysis Agent: documents flows, scores complexity, maps connectors."""
from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph, END

from app.agents.base_agent import AgentState, BaseAgent
from app.services.ai_provider import get_ai_service
from app.utils.logging import get_logger

logger = get_logger(__name__)


class FlowAnalysisAgent(BaseAgent):
    name = "flow_analysis_agent"

    def _build_graph(self) -> Any:
        graph = StateGraph(AgentState)
        graph.add_node("analyze_flows", self._analyze_flows)
        graph.add_node("score_complexity", self._score_complexity)
        graph.add_node("map_connectors", self._map_connectors)
        graph.add_node("generate_docs", self._generate_docs)

        graph.set_entry_point("analyze_flows")
        graph.add_edge("analyze_flows", "score_complexity")
        graph.add_edge("score_complexity", "map_connectors")
        graph.add_edge("map_connectors", "generate_docs")
        graph.add_edge("generate_docs", END)

        return graph.compile()

    async def _analyze_flows(self, state: AgentState) -> AgentState:
        flows = state.get("flows", [])
        state["current_step"] = "analyze_flows"
        logger.info("analyzing_flows", count=len(flows))

        analyzed = []
        for flow in flows:
            analysis = {
                **flow,
                "has_source": self._has_source(flow),
                "is_api_flow": self._is_api_flow(flow),
                "uses_dataweave": flow.get("has_dataweave", False),
                "connector_count": len(flow.get("connectors_used", [])),
                "error_handler_count": len(flow.get("error_handlers", [])),
            }
            analyzed.append(analysis)

        state["flows"] = analyzed
        return state

    async def _score_complexity(self, state: AgentState) -> AgentState:
        state["current_step"] = "score_complexity"
        complexity_map = {}

        for flow in state.get("flows", []):
            score = self._compute_complexity(flow)
            complexity_map[flow.get("name", "")] = score

        state["complexity_map"] = complexity_map
        return state

    async def _map_connectors(self, state: AgentState) -> AgentState:
        state["current_step"] = "map_connectors"
        connector_usage: dict[str, list[str]] = {}

        for flow in state.get("flows", []):
            for connector in flow.get("connectors_used", []):
                connector_usage.setdefault(connector, [])
                connector_usage[connector].append(flow.get("name", ""))

        app_meta = state.get("app_metadata", {})
        app_meta["connector_usage"] = connector_usage
        state["app_metadata"] = app_meta
        return state

    async def _generate_docs(self, state: AgentState) -> AgentState:
        state["current_step"] = "generate_docs"
        ai_service = get_ai_service()
        flow_docs: dict[str, str] = {}

        # Document top 20 flows by complexity to avoid rate limits
        flows = state.get("flows", [])
        complexity = state.get("complexity_map", {})
        top_flows = sorted(flows, key=lambda f: complexity.get(f.get("name", ""), 0), reverse=True)[:20]

        for flow in top_flows:
            flow_name = flow.get("name", "")
            flow_xml = flow.get("raw_xml", "")
            if flow_xml:
                try:
                    doc = await ai_service.document_flow(flow_name, flow_xml)
                    flow_docs[flow_name] = doc
                except Exception as e:
                    logger.warning("flow_doc_error", flow=flow_name, error=str(e))
                    flow_docs[flow_name] = f"Auto-documentation failed: {e}"

        state["flow_docs"] = flow_docs
        logger.info("docs_generated", count=len(flow_docs))
        return state

    def _has_source(self, flow: dict) -> bool:
        """Check if flow has a message source (HTTP listener, scheduler, etc.)."""
        processors = flow.get("processors", [])
        if processors:
            first = processors[0]
            return first.get("connector") in {"http", "scheduler", "jms", "kafka", "vm"}
        return False

    def _is_api_flow(self, flow: dict) -> bool:
        return "http" in flow.get("connectors_used", []) and self._has_source(flow)

    def _compute_complexity(self, flow: dict) -> int:
        """McCabe-inspired complexity for Mule flows (1-10 scale)."""
        score = 1
        processors = flow.get("processors", [])
        score += len(processors) // 3
        score += len(flow.get("connectors_used", []))
        score += 2 if flow.get("has_dataweave") else 0
        score += len(flow.get("error_handlers", []))
        return min(score, 10)
