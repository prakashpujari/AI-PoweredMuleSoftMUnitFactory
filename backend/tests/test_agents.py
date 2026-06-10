"""Unit tests for LangGraph agents (mocked AI calls)."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.coverage_agent import CoverageAgent
from app.agents.failure_analysis_agent import FailureAnalysisAgent
from app.agents.executive_reporting_agent import ExecutiveReportingAgent
from app.agents.migration_agent import MigrationAgent


# ── CoverageAgent tests ────────────────────────────────────────────────────

class TestCoverageAgent:
    @pytest.mark.asyncio
    async def test_full_coverage_when_all_flows_tested(self):
        agent = CoverageAgent()
        state = await agent.run({
            "flows": [
                {"name": "flow-a", "flow_type": "flow", "processor_count": 5, "has_error_handler": False},
                {"name": "flow-b", "flow_type": "flow", "processor_count": 3, "has_error_handler": True},
            ],
            "test_cases": [
                {"flow_name": "flow-a", "test_types": ["happy_path"]},
                {"flow_name": "flow-b", "test_types": ["happy_path", "error_handling"]},
            ],
            "config": {},
        })
        report = state["coverage_report"]
        assert report["flow_coverage"] == 100.0
        assert report["covered_flows"] == 2

    @pytest.mark.asyncio
    async def test_zero_coverage_when_no_tests(self):
        agent = CoverageAgent()
        state = await agent.run({
            "flows": [
                {"name": "flow-a", "flow_type": "flow", "processor_count": 5, "has_error_handler": False},
            ],
            "test_cases": [],
            "config": {},
        })
        report = state["coverage_report"]
        assert report["flow_coverage"] == 0.0
        assert "flow-a" in report["uncovered_flows"]

    @pytest.mark.asyncio
    async def test_meets_target_flag(self):
        agent = CoverageAgent()
        flows = [
            {"name": f"flow-{i}", "flow_type": "flow", "processor_count": 2, "has_error_handler": False}
            for i in range(10)
        ]
        test_cases = [
            {"flow_name": f"flow-{i}", "test_types": ["happy_path"]}
            for i in range(10)
        ]
        state = await agent.run({"flows": flows, "test_cases": test_cases, "config": {}})
        assert state["coverage_report"]["meets_target"] is True

    @pytest.mark.asyncio
    async def test_coverage_gaps_identified(self):
        agent = CoverageAgent()
        state = await agent.run({
            "flows": [
                {"name": "flow-untested", "flow_type": "flow", "processor_count": 3, "has_error_handler": False},
            ],
            "test_cases": [],
            "config": {},
        })
        assert len(state["coverage_report"]["coverage_gaps"]) > 0


# ── FailureAnalysisAgent tests ─────────────────────────────────────────────

class TestFailureAnalysisAgent:
    @pytest.mark.asyncio
    async def test_no_failures_empty_analyses(self):
        agent = FailureAnalysisAgent()
        state = await agent.run({
            "surefire_results": {"test_suites": [], "total": 10, "passed": 10, "failed": 0},
            "config": {},
        })
        assert state["failure_analyses"] == []
        assert state["failure_summary"]["total_failures"] == 0

    @pytest.mark.asyncio
    async def test_flaky_detection_keyword(self):
        agent = FailureAnalysisAgent()
        # Inject pre-analyzed state to test flaky detection node
        state = {
            "raw_failures": [],
            "failure_analyses": [
                {"test_name": "test-1", "root_cause": "connection timeout occurred", "severity": "medium", "confidence_score": 0.8},
            ],
            "surefire_results": {"test_suites": []},
            "config": {},
        }
        # Run only the flaky detection step
        with patch.object(agent, "_extract_failures", return_value=state):
            with patch.object(agent, "_analyze_with_llm", return_value=state):
                result_state = await agent._detect_flakiness(state)
                assert result_state["failure_analyses"][0]["is_flaky"] is True

    @pytest.mark.asyncio
    async def test_failure_summary_counts(self):
        agent = FailureAnalysisAgent()
        state = {
            "raw_failures": [],
            "failure_analyses": [
                {"test_name": "a", "severity": "critical", "confidence_score": 0.9, "is_flaky": False, "failure_category": "config"},
                {"test_name": "b", "severity": "high", "confidence_score": 0.7, "is_flaky": True, "failure_category": "network"},
                {"test_name": "c", "severity": "low", "confidence_score": 0.5, "is_flaky": False, "failure_category": "config"},
            ],
        }
        result = await agent._categorize_failures(state)
        summary = result["failure_summary"]
        assert summary["total_failures"] == 3
        assert summary["critical"] == 1
        assert summary["flaky"] == 1


# ── ExecutiveReportingAgent tests ──────────────────────────────────────────

class TestExecutiveReportingAgent:
    def setup_method(self):
        self.agent = ExecutiveReportingAgent()

    def test_letter_grade_A(self):
        assert self.agent._letter_grade(95) == "A"

    def test_letter_grade_B(self):
        assert self.agent._letter_grade(85) == "B"

    def test_letter_grade_F(self):
        assert self.agent._letter_grade(50) == "F"

    def test_recommendation_approved(self):
        assert self.agent._recommendation(95, 10) == "APPROVED FOR PRODUCTION"

    def test_recommendation_not_ready(self):
        assert self.agent._recommendation(40, 80) == "NOT READY FOR PRODUCTION"

    def test_risk_level_low(self):
        assert self.agent._risk_level(10) == "LOW"

    def test_risk_level_critical(self):
        assert self.agent._risk_level(85) == "CRITICAL"

    @pytest.mark.asyncio
    async def test_scores_computed_from_metrics(self):
        state = {
            "aggregated_metrics": {
                "total_tests": 100,
                "passed_tests": 95,
                "failed_tests": 5,
                "pass_rate": 95.0,
                "overall_coverage": 92.0,
            },
            "coverage_report": {"meets_target": False, "coverage_gaps": []},
            "failure_summary": {"critical": 0, "high": 1},
            "flows": [],
            "test_cases": [],
        }
        result = await self.agent._compute_scores(state)
        scores = result["scores"]
        assert "production_readiness_score" in scores
        assert 0 <= scores["production_readiness_score"] <= 100


# ── MigrationAgent tests ───────────────────────────────────────────────────

class TestMigrationAgent:
    @pytest.mark.asyncio
    async def test_java_risks_for_old_version(self):
        agent = MigrationAgent()
        state = {
            "migration_context": {
                "java_version": "11",
                "target_version": "4.9.0",
                "source_version": "4.6.0",
            }
        }
        result = await agent._check_java_compatibility(state)
        assert len(result["migration_context"]["java_version_risks"]) > 0

    @pytest.mark.asyncio
    async def test_no_java_risks_for_java17(self):
        agent = MigrationAgent()
        state = {
            "migration_context": {
                "java_version": "17",
                "target_version": "4.9.0",
                "source_version": "4.6.0",
            }
        }
        result = await agent._check_java_compatibility(state)
        assert len(result["migration_context"]["java_version_risks"]) == 0
