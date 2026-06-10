"""Agent 5 — Execution Agent: runs `mvn clean test` and collects Surefire/MUnit reports."""
from __future__ import annotations

import asyncio
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, END

from app.agents.base_agent import AgentState, BaseAgent
from app.config import get_settings
from app.utils.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

SUREFIRE_RESULT_RE = re.compile(
    r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)"
)


class ExecutionAgent(BaseAgent):
    name = "execution_agent"

    def _build_graph(self) -> Any:
        graph = StateGraph(AgentState)
        graph.add_node("prepare_execution", self._prepare_execution)
        graph.add_node("run_maven", self._run_maven)
        graph.add_node("collect_surefire", self._collect_surefire_reports)
        graph.add_node("collect_munit", self._collect_munit_reports)
        graph.add_node("summarize_results", self._summarize_results)

        graph.set_entry_point("prepare_execution")
        graph.add_edge("prepare_execution", "run_maven")
        graph.add_edge("run_maven", "collect_surefire")
        graph.add_edge("collect_surefire", "collect_munit")
        graph.add_edge("collect_munit", "summarize_results")
        graph.add_edge("summarize_results", END)

        return graph.compile()

    async def _prepare_execution(self, state: AgentState) -> AgentState:
        state["current_step"] = "prepare_execution"
        repo_path = state.get("repo_path", "")

        if not Path(repo_path).exists():
            return self._record_error(state, f"Repo path not found: {repo_path}")

        # Ensure test directory has MUnit files
        test_dir = Path(repo_path) / "src" / "test" / "munit"
        if not test_dir.exists() or not list(test_dir.glob("*.xml")):
            logger.warning("no_munit_files", path=str(test_dir))

        logger.info("execution_prepared", path=repo_path)
        return state

    async def _run_maven(self, state: AgentState) -> AgentState:
        state["current_step"] = "run_maven"
        repo_path = state.get("repo_path", "")
        cfg = state.get("config", {})

        env = os.environ.copy()
        env["MAVEN_OPTS"] = settings.MVN_OPTS

        maven_cmd = cfg.get("maven_command", "mvn clean test -B -Dmule.test.skip=false")
        logger.info("running_maven", cmd=maven_cmd, path=repo_path)

        try:
            proc = await asyncio.create_subprocess_shell(
                maven_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=repo_path,
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            state["maven_output"] = stdout_str
            state["maven_stderr"] = stderr_str
            state["maven_return_code"] = proc.returncode

            if proc.returncode != 0:
                logger.warning("maven_failed", return_code=proc.returncode)
            else:
                logger.info("maven_success")

        except asyncio.TimeoutError:
            return self._record_error(state, "Maven execution timed out after 10 minutes")
        except Exception as e:
            return self._record_error(state, f"Maven execution error: {e}")

        return state

    async def _collect_surefire_reports(self, state: AgentState) -> AgentState:
        state["current_step"] = "collect_surefire"
        repo_path = state.get("repo_path", "")
        surefire_dir = Path(repo_path) / "target" / "surefire-reports"

        results: dict[str, Any] = {
            "test_suites": [],
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
        }

        if surefire_dir.exists():
            for xml_file in surefire_dir.glob("TEST-*.xml"):
                try:
                    suite_data = self._parse_surefire_xml(xml_file)
                    results["test_suites"].append(suite_data)
                    results["total"] += suite_data["tests"]
                    results["passed"] += suite_data["passed"]
                    results["failed"] += suite_data["failures"]
                    results["errors"] += suite_data["errors"]
                    results["skipped"] += suite_data["skipped"]
                except Exception as e:
                    logger.warning("surefire_parse_error", file=str(xml_file), error=str(e))

        state["surefire_results"] = results
        logger.info("surefire_collected", total=results["total"], failed=results["failed"])
        return state

    async def _collect_munit_reports(self, state: AgentState) -> AgentState:
        state["current_step"] = "collect_munit"
        repo_path = state.get("repo_path", "")
        munit_dir = Path(repo_path) / "target" / "site" / "munit"

        results: dict[str, Any] = {"reports": [], "coverage": {}}

        if munit_dir.exists():
            for report_file in munit_dir.glob("**/*.json"):
                try:
                    import json
                    data = json.loads(report_file.read_text(encoding="utf-8"))
                    results["reports"].append(data)
                except Exception as e:
                    logger.warning("munit_report_parse_error", file=str(report_file), error=str(e))

        state["munit_results"] = results
        return state

    async def _summarize_results(self, state: AgentState) -> AgentState:
        state["current_step"] = "summarize_results"
        surefire = state.get("surefire_results", {})

        total = surefire.get("total", 0)
        passed = surefire.get("passed", 0)
        failed = surefire.get("failed", 0)
        errors_count = surefire.get("errors", 0)
        skipped = surefire.get("skipped", 0)

        pass_rate = (passed / total * 100) if total > 0 else 0.0

        state["execution_summary"] = {
            "total_tests": total,
            "passed": passed,
            "failed": failed + errors_count,
            "skipped": skipped,
            "pass_rate": round(pass_rate, 2),
            "maven_return_code": state.get("maven_return_code", -1),
        }

        logger.info(
            "execution_summary",
            total=total,
            passed=passed,
            failed=failed,
            pass_rate=pass_rate,
        )
        return state

    def _parse_surefire_xml(self, xml_path: Path) -> dict[str, Any]:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        tests = int(root.get("tests", 0))
        failures = int(root.get("failures", 0))
        errors = int(root.get("errors", 0))
        skipped = int(root.get("skipped", 0))
        passed = tests - failures - errors - skipped

        return {
            "name": root.get("name", ""),
            "tests": tests,
            "passed": max(0, passed),
            "failures": failures,
            "errors": errors,
            "skipped": skipped,
            "time": float(root.get("time", 0)),
        }
