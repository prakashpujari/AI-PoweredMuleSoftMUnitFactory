"""Agent 3 — MUnit Generation Agent: AI-generates complete MUnit test suites."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, END

from app.agents.base_agent import AgentState, BaseAgent
from app.parsers.mule_xml_parser import FlowInfo
from app.parsers.raml_parser import RamlSpec
from app.services.munit_generator import GenerationRequest, MUnitGenerator
from app.utils.logging import get_logger

logger = get_logger(__name__)


class MUnitGenerationAgent(BaseAgent):
    name = "munit_generation_agent"

    def __init__(self) -> None:
        self._generator = MUnitGenerator()
        super().__init__()

    def _build_graph(self) -> Any:
        graph = StateGraph(AgentState)
        graph.add_node("select_flows", self._select_flows_for_generation)
        graph.add_node("generate_tests", self._generate_tests)
        graph.add_node("write_test_files", self._write_test_files)
        graph.add_node("validate_xml", self._validate_xml)

        graph.set_entry_point("select_flows")
        graph.add_edge("select_flows", "generate_tests")
        graph.add_edge("generate_tests", "write_test_files")
        graph.add_edge("write_test_files", "validate_xml")
        graph.add_edge("validate_xml", END)

        return graph.compile()

    async def _select_flows_for_generation(self, state: AgentState) -> AgentState:
        state["current_step"] = "select_flows"
        flows = state.get("flows", [])
        cfg = state.get("config", {})

        # Filter: skip already-covered flows in re-generation scenarios
        selected = [f for f in flows if f.get("flow_type") != "error_handler"]
        state["flows"] = selected
        logger.info("flows_selected_for_generation", count=len(selected))
        return state

    async def _generate_tests(self, state: AgentState) -> AgentState:
        state["current_step"] = "generate_tests"
        flows = state.get("flows", [])
        cfg = state.get("config", {})
        raml_spec_dict = state.get("raml_spec", {})
        ai_provider = cfg.get("ai_provider", "groq")
        app_name = state.get("app_metadata", {}).get("name", "")

        raml_spec = None
        if raml_spec_dict:
            raml_spec = RamlSpec()
            raml_spec.title = raml_spec_dict.get("title", "")

        test_cases: list[dict] = []

        for flow_dict in flows:
            flow = FlowInfo()
            flow.name = flow_dict.get("name", "")
            flow.flow_type = flow_dict.get("flow_type", "flow")
            flow.connectors_used = flow_dict.get("connectors_used", [])
            flow.raw_xml = flow_dict.get("raw_xml", "")
            flow.has_dataweave = flow_dict.get("has_dataweave", False)
            flow.has_error_handler = flow_dict.get("has_error_handler", False)

            test_types = self._generator.build_test_types_for_flow(flow)

            request = GenerationRequest(
                flow_info=flow,
                test_types=test_types,
                raml_spec=raml_spec,
                ai_provider=ai_provider,
                application_name=app_name,
            )

            result = await self._generator.generate(request)
            test_cases.append({
                "flow_name": result.flow_name,
                "munit_xml": result.munit_xml,
                "test_types": result.test_types,
                "test_count": result.test_count,
                "confidence_score": result.confidence_score,
                "ai_model": result.ai_model,
                "errors": result.errors,
            })

        state["test_cases"] = test_cases
        total_tests = sum(tc["test_count"] for tc in test_cases)
        logger.info("tests_generated", flows=len(test_cases), total_tests=total_tests)
        return state

    async def _write_test_files(self, state: AgentState) -> AgentState:
        state["current_step"] = "write_test_files"
        repo_path = state.get("repo_path", "")
        test_cases = state.get("test_cases", [])
        munit_files: dict[str, str] = {}

        if repo_path:
            test_dir = Path(repo_path) / "src" / "test" / "munit"
            test_dir.mkdir(parents=True, exist_ok=True)

            for tc in test_cases:
                flow_name = tc["flow_name"].lower().replace(" ", "-").replace("_", "-")
                file_path = test_dir / f"{flow_name}-test.xml"
                file_path.write_text(tc["munit_xml"], encoding="utf-8")
                munit_files[tc["flow_name"]] = str(file_path)

        state["munit_files"] = munit_files
        logger.info("munit_files_written", count=len(munit_files))
        return state

    async def _validate_xml(self, state: AgentState) -> AgentState:
        state["current_step"] = "validate_xml"
        from lxml import etree

        test_cases = state.get("test_cases", [])
        valid_count = 0

        for tc in test_cases:
            try:
                etree.fromstring(tc["munit_xml"].encode("utf-8"))
                tc["xml_valid"] = True
                valid_count += 1
            except etree.XMLSyntaxError as e:
                tc["xml_valid"] = False
                tc["xml_error"] = str(e)
                logger.warning("munit_xml_invalid", flow=tc["flow_name"], error=str(e))

        logger.info("xml_validation_complete", valid=valid_count, total=len(test_cases))
        state["test_cases"] = test_cases
        return state
