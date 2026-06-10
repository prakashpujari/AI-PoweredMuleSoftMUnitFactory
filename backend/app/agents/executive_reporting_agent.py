"""Agent 8 — Executive Reporting Agent: generates dashboards, PDF reports, scorecards."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, END

from app.agents.base_agent import AgentState, BaseAgent
from app.config import get_settings
from app.services.ai_provider import get_ai_service
from app.utils.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class ExecutiveReportingAgent(BaseAgent):
    name = "executive_reporting_agent"

    def _build_graph(self) -> Any:
        graph = StateGraph(AgentState)
        graph.add_node("aggregate_metrics", self._aggregate_metrics)
        graph.add_node("compute_scores", self._compute_scores)
        graph.add_node("generate_ai_narrative", self._generate_ai_narrative)
        graph.add_node("build_dashboard_data", self._build_dashboard_data)
        graph.add_node("generate_pdf_report", self._generate_pdf_report)

        graph.set_entry_point("aggregate_metrics")
        graph.add_edge("aggregate_metrics", "compute_scores")
        graph.add_edge("compute_scores", "generate_ai_narrative")
        graph.add_edge("generate_ai_narrative", "build_dashboard_data")
        graph.add_edge("build_dashboard_data", "generate_pdf_report")
        graph.add_edge("generate_pdf_report", END)

        return graph.compile()

    async def _aggregate_metrics(self, state: AgentState) -> AgentState:
        state["current_step"] = "aggregate_metrics"
        execution = state.get("execution_summary", {})
        coverage = state.get("coverage_report", {})
        failures = state.get("failure_summary", {})
        migration = state.get("migration_report", {})
        flows = state.get("flows", [])

        state["aggregated_metrics"] = {
            "total_tests": execution.get("total_tests", 0),
            "passed_tests": execution.get("passed", 0),
            "failed_tests": execution.get("failed", 0),
            "skipped_tests": execution.get("skipped", 0),
            "pass_rate": execution.get("pass_rate", 0.0),
            "overall_coverage": coverage.get("overall_coverage", 0.0),
            "flow_coverage": coverage.get("flow_coverage", 0.0),
            "processor_coverage": coverage.get("processor_coverage", 0.0),
            "total_flows": len(flows),
            "critical_failures": failures.get("critical", 0),
            "high_failures": failures.get("high", 0),
            "migration_readiness": migration.get("migration_readiness_score", 0),
            "migration_risk": migration.get("overall_risk", "unknown"),
        }
        return state

    async def _compute_scores(self, state: AgentState) -> AgentState:
        state["current_step"] = "compute_scores"
        metrics = state.get("aggregated_metrics", {})
        coverage = state.get("coverage_report", {})
        failures = state.get("failure_summary", {})

        # Security Score (0-100): based on security test presence and pass rates
        security_score = self._score_security(state)

        # Performance Score (0-100)
        perf_score = self._score_performance(state)

        # Quality Score (0-100): weighted coverage + pass rate
        quality_score = round(
            metrics.get("overall_coverage", 0) * 0.5
            + metrics.get("pass_rate", 0) * 0.5,
            1,
        )

        # Production Readiness (0-100)
        prod_readiness = self._score_production_readiness(metrics, security_score, quality_score)

        # Risk Score (0-100, lower = better)
        risk_score = self._score_risk(metrics, failures)

        state["scores"] = {
            "security_score": security_score,
            "performance_score": perf_score,
            "quality_score": quality_score,
            "production_readiness_score": prod_readiness,
            "risk_score": risk_score,
            "overall_grade": self._letter_grade(prod_readiness),
            "recommendation": self._recommendation(prod_readiness, risk_score),
            "risk_level": self._risk_level(risk_score),
        }

        logger.info("scores_computed", scores=state["scores"])
        return state

    async def _generate_ai_narrative(self, state: AgentState) -> AgentState:
        state["current_step"] = "generate_ai_narrative"
        metrics = state.get("aggregated_metrics", {})
        app_meta = state.get("app_metadata", {})

        try:
            ai_service = get_ai_service()
            narrative = await ai_service.generate_executive_summary(
                metrics={**metrics, **state.get("scores", {})},
                applications=[app_meta],
            )
            state["executive_summary"] = narrative
        except Exception as e:
            logger.warning("narrative_generation_error", error=str(e))
            m = metrics
            state["executive_summary"] = (
                f"Test execution completed with {m.get('pass_rate', 0):.1f}% pass rate "
                f"and {m.get('overall_coverage', 0):.1f}% coverage across "
                f"{m.get('total_flows', 0)} flows."
            )

        return state

    async def _build_dashboard_data(self, state: AgentState) -> AgentState:
        state["current_step"] = "build_dashboard_data"
        metrics = state.get("aggregated_metrics", {})
        scores = state.get("scores", {})
        coverage = state.get("coverage_report", {})
        migration = state.get("migration_report", {})
        failures = state.get("failure_analyses", [])

        state["dashboard_data"] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "application": state.get("app_metadata", {}),
            "summary": {
                **metrics,
                **scores,
            },
            "coverage": {
                "overall": coverage.get("overall_coverage", 0),
                "flow": coverage.get("flow_coverage", 0),
                "processor": coverage.get("processor_coverage", 0),
                "error_handler": coverage.get("error_handler_coverage", 0),
                "meets_target": coverage.get("meets_target", False),
                "gaps": coverage.get("coverage_gaps", [])[:10],
            },
            "top_failures": [
                {
                    "test": f.get("test_name", ""),
                    "severity": f.get("severity", ""),
                    "root_cause": f.get("root_cause", "")[:200],
                }
                for f in failures[:10]
            ],
            "migration": {
                "source_version": migration.get("source_version", ""),
                "target_version": migration.get("target_version", ""),
                "risk": migration.get("overall_risk", ""),
                "readiness_score": migration.get("migration_readiness_score", 0),
                "effort_days": migration.get("estimated_effort_days", 0),
            },
            "executive_summary": state.get("executive_summary", ""),
            "recommendations": coverage.get("ai_recommendations", ""),
        }

        return state

    async def _generate_pdf_report(self, state: AgentState) -> AgentState:
        state["current_step"] = "generate_pdf_report"
        repo_path = state.get("repo_path", "/tmp")
        dashboard = state.get("dashboard_data", {})
        scores = state.get("scores", {})

        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

            output_path = Path(repo_path) / "target" / "ai-munit-factory-report.pdf"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            doc = SimpleDocTemplate(str(output_path), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=24, spaceAfter=20)
            story.append(Paragraph("AI-MUnit-Factory Executive Report", title_style))
            story.append(Paragraph(f"Generated: {dashboard.get('generated_at', '')}", styles["Normal"]))
            story.append(Spacer(1, 0.3 * inch))

            # Executive Summary
            story.append(Paragraph("Executive Summary", styles["Heading2"]))
            story.append(Paragraph(dashboard.get("executive_summary", ""), styles["Normal"]))
            story.append(Spacer(1, 0.2 * inch))

            # Scorecard table
            summary = dashboard.get("summary", {})
            score_data = [
                ["Metric", "Value", "Status"],
                ["Total Tests", str(summary.get("total_tests", 0)), ""],
                ["Tests Passed", str(summary.get("passed_tests", 0)), "✓"],
                ["Tests Failed", str(summary.get("failed_tests", 0)), "✗" if summary.get("failed_tests", 0) > 0 else "✓"],
                ["Pass Rate", f"{summary.get('pass_rate', 0):.1f}%", ""],
                ["Overall Coverage", f"{summary.get('overall_coverage', 0):.1f}%", ""],
                ["Security Score", f"{summary.get('security_score', 0)}/100", ""],
                ["Performance Score", f"{summary.get('performance_score', 0)}/100", ""],
                ["Production Readiness", f"{summary.get('production_readiness_score', 0)}/100", ""],
                ["Risk Level", summary.get("risk_level", ""), ""],
                ["Recommendation", summary.get("recommendation", ""), ""],
            ]

            t = Table(score_data, colWidths=[3 * inch, 2 * inch, 1.5 * inch])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                ("BOX", (0, 0), (-1, -1), 1, colors.grey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(Paragraph("Test Results Scorecard", styles["Heading2"]))
            story.append(t)

            doc.build(story)
            state["pdf_report_path"] = str(output_path)
            logger.info("pdf_generated", path=str(output_path))

        except Exception as e:
            logger.warning("pdf_generation_error", error=str(e))
            state["pdf_report_path"] = ""

        return state

    def _score_security(self, state: AgentState) -> float:
        test_cases = state.get("test_cases", [])
        security_types = {"oauth_failure", "jwt_failure", "client_id_failure", "security", "rate_limit"}
        security_tests = sum(
            1 for tc in test_cases
            if any(t in security_types for t in tc.get("test_types", []))
        )
        base = min(security_tests * 5, 80)
        flows = state.get("flows", [])
        has_security_flows = any(
            "http" in f.get("connectors_used", []) for f in flows
        )
        return round(base + (20 if has_security_flows else 0), 1)

    def _score_performance(self, state: AgentState) -> float:
        execution = state.get("execution_summary", {})
        pass_rate = execution.get("pass_rate", 0)
        return round(min(pass_rate * 0.9 + 10, 100), 1)

    def _score_production_readiness(self, metrics: dict, security: float, quality: float) -> float:
        score = (
            quality * 0.40
            + security * 0.30
            + min(metrics.get("pass_rate", 0), 100) * 0.20
            + min(metrics.get("overall_coverage", 0), 100) * 0.10
        )
        return round(min(score, 100), 1)

    def _score_risk(self, metrics: dict, failures: dict) -> float:
        risk = 0.0
        risk += failures.get("critical", 0) * 20
        risk += failures.get("high", 0) * 10
        risk += max(0, (100 - metrics.get("overall_coverage", 0)) * 0.3)
        risk += max(0, (100 - metrics.get("pass_rate", 0)) * 0.5)
        return round(min(risk, 100), 1)

    def _letter_grade(self, score: float) -> str:
        if score >= 90: return "A"
        if score >= 80: return "B"
        if score >= 70: return "C"
        if score >= 60: return "D"
        return "F"

    def _recommendation(self, readiness: float, risk: float) -> str:
        if readiness >= 90 and risk < 20:
            return "APPROVED FOR PRODUCTION"
        if readiness >= 75 and risk < 40:
            return "CONDITIONAL APPROVAL — ADDRESS HIGH RISKS"
        if readiness >= 60:
            return "ADDITIONAL TESTING REQUIRED"
        return "NOT READY FOR PRODUCTION"

    def _risk_level(self, risk_score: float) -> str:
        if risk_score < 20: return "LOW"
        if risk_score < 50: return "MEDIUM"
        if risk_score < 75: return "HIGH"
        return "CRITICAL"
