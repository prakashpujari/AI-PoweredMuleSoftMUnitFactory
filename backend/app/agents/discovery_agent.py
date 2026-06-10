"""Agent 1 — Mule Discovery Agent: scans repos, parses pom.xml, RAML, mule-artifact.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, END

from app.agents.base_agent import AgentState, BaseAgent
from app.parsers import PomParser, MuleXmlParser, RamlParser
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DiscoveryAgent(BaseAgent):
    name = "discovery_agent"

    def __init__(self) -> None:
        self._pom_parser = PomParser()
        self._xml_parser = MuleXmlParser()
        self._raml_parser = RamlParser()
        super().__init__()

    def _build_graph(self) -> Any:
        graph = StateGraph(AgentState)
        graph.add_node("scan_repository", self._scan_repository)
        graph.add_node("parse_pom", self._parse_pom)
        graph.add_node("parse_mule_xml", self._parse_mule_xml)
        graph.add_node("parse_raml", self._parse_raml)
        graph.add_node("parse_artifact_json", self._parse_artifact_json)
        graph.add_node("build_inventory", self._build_inventory)

        graph.set_entry_point("scan_repository")
        graph.add_edge("scan_repository", "parse_pom")
        graph.add_edge("parse_pom", "parse_mule_xml")
        graph.add_edge("parse_mule_xml", "parse_raml")
        graph.add_edge("parse_raml", "parse_artifact_json")
        graph.add_edge("parse_artifact_json", "build_inventory")
        graph.add_edge("build_inventory", END)

        return graph.compile()

    async def _scan_repository(self, state: AgentState) -> AgentState:
        repo_path = state.get("repo_path", "")
        path = Path(repo_path)
        state["current_step"] = "scan_repository"

        if not path.exists():
            return self._record_error(state, f"Repository path not found: {repo_path}")

        logger.info("scanning_repo", path=repo_path)
        state["app_metadata"] = {"repo_path": repo_path, "exists": True}
        return state

    async def _parse_pom(self, state: AgentState) -> AgentState:
        repo_path = state.get("repo_path", "")
        state["current_step"] = "parse_pom"
        pom_path = Path(repo_path) / "pom.xml"

        if not pom_path.exists():
            logger.warning("pom_not_found", path=str(pom_path))
            state["pom_metadata"] = {}
            return state

        try:
            meta = self._pom_parser.parse_file(pom_path)
            state["pom_metadata"] = meta.to_dict()
            logger.info("pom_parsed", artifact=meta.artifact_id, runtime=meta.mule_runtime_version)
        except Exception as e:
            return self._record_error(state, f"POM parse error: {e}")

        return state

    async def _parse_mule_xml(self, state: AgentState) -> AgentState:
        repo_path = state.get("repo_path", "")
        state["current_step"] = "parse_mule_xml"

        src_dirs = [
            Path(repo_path) / "src" / "main" / "mule",
            Path(repo_path) / "src" / "main" / "resources",
        ]

        all_flows = []
        for src_dir in src_dirs:
            if src_dir.exists():
                try:
                    flows = self._xml_parser.parse_directory(src_dir)
                    all_flows.extend([f.to_dict() for f in flows])
                except Exception as e:
                    self._record_error(state, f"XML parse error in {src_dir}: {e}")

        state["flows"] = all_flows
        logger.info("flows_discovered", count=len(all_flows))
        return state

    async def _parse_raml(self, state: AgentState) -> AgentState:
        repo_path = state.get("repo_path", "")
        state["current_step"] = "parse_raml"

        raml_dirs = [
            Path(repo_path) / "src" / "main" / "resources" / "api",
            Path(repo_path) / "api",
        ]

        for raml_dir in raml_dirs:
            if raml_dir.exists():
                raml_files = list(raml_dir.glob("*.raml"))
                if raml_files:
                    try:
                        spec = self._raml_parser.parse_file(raml_files[0])
                        state["raml_spec"] = spec.to_dict()
                        logger.info("raml_parsed", file=str(raml_files[0]))
                        return state
                    except Exception as e:
                        self._record_error(state, f"RAML parse error: {e}")

        state["raml_spec"] = {}
        return state

    async def _parse_artifact_json(self, state: AgentState) -> AgentState:
        repo_path = state.get("repo_path", "")
        state["current_step"] = "parse_artifact_json"

        artifact_path = Path(repo_path) / "mule-artifact.json"
        if artifact_path.exists():
            try:
                data = json.loads(artifact_path.read_text(encoding="utf-8"))
                app_meta = state.get("app_metadata", {})
                app_meta["mule_artifact"] = data
                state["app_metadata"] = app_meta
                logger.info("artifact_json_parsed", data=data)
            except Exception as e:
                self._record_error(state, f"mule-artifact.json parse error: {e}")

        return state

    async def _build_inventory(self, state: AgentState) -> AgentState:
        state["current_step"] = "build_inventory"
        pom = state.get("pom_metadata", {})
        flows = state.get("flows", [])
        raml = state.get("raml_spec", {})

        connectors: set[str] = set()
        for flow in flows:
            connectors.update(flow.get("connectors_used", []))

        all_meta = state.get("app_metadata", {})
        all_meta.update({
            "name": pom.get("artifact_id", "unknown"),
            "group_id": pom.get("group_id", ""),
            "version": pom.get("version", ""),
            "mule_runtime_version": pom.get("mule_runtime_version", ""),
            "flows_count": len(flows),
            "connectors": sorted(connectors),
            "has_raml": bool(raml),
            "api_title": raml.get("title", ""),
        })
        state["app_metadata"] = all_meta
        logger.info("inventory_built", name=all_meta["name"], flows=len(flows), connectors=list(connectors))
        return state
