"""Groq AI service — primary AI provider using llama-3.3-70b-versatile."""
from __future__ import annotations

import json
from typing import Any

from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings
from app.utils.exceptions import AIProviderError
from app.utils.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class GroqService:
    """All AI generation tasks delegated to Groq llama-3.3-70b-versatile."""

    def __init__(self) -> None:
        self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self._model = settings.GROQ_MODEL
        self._max_tokens = settings.GROQ_MAX_TOKENS
        self._temperature = settings.GROQ_TEMPERATURE

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _chat(self, system: str, user: str, temperature: float | None = None) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature if temperature is not None else self._temperature,
                max_tokens=self._max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("groq_api_error", error=str(e), model=self._model)
            raise AIProviderError(f"Groq API error: {e}")

    async def generate_munit(
        self,
        flow_name: str,
        flow_xml: str,
        connectors: list[str],
        test_types: list[str],
        raml_spec: str = "",
    ) -> str:
        """Generate complete MUnit XML test suite for a Mule flow."""
        system = """You are a Principal MuleSoft Test Architect with 15+ years of experience.
Generate production-grade MUnit 2.x test suites in valid Mule 4 XML format.
Always include:
- Proper namespace declarations
- Mock processors for all external dependencies
- Clear assertions using MUnit matchers
- Both happy path and negative path tests
- Error handler coverage
Output ONLY valid MUnit XML, no markdown or explanations."""

        connectors_str = ", ".join(connectors) if connectors else "none"
        test_types_str = "\n".join(f"- {t}" for t in test_types)

        user = f"""Generate comprehensive MUnit tests for this Mule 4 flow.

Flow Name: {flow_name}
Connectors Used: {connectors_str}
Required Test Types:
{test_types_str}

{"RAML Specification:\n" + raml_spec if raml_spec else ""}

Mule Flow XML:
{flow_xml}

Generate complete MUnit XML with all test cases. Include:
1. xmlns declarations for munit, munit-tools, http, db, etc.
2. Mock event processors for each connector
3. Assertions for status codes, payload, variables
4. Error scenario tests
5. Security test cases if OAuth/JWT connectors present"""

        logger.info("generating_munit", flow=flow_name, test_types=len(test_types))
        return await self._chat(system, user)

    async def analyze_failure(
        self,
        test_name: str,
        error_message: str,
        stack_trace: str,
        flow_xml: str,
        munit_xml: str,
    ) -> dict[str, Any]:
        """Analyze a test failure and return root cause + fix."""
        system = """You are a Senior MuleSoft Debugging Expert.
Analyze test failures and return a JSON object with these exact keys:
{
  "root_cause": "...",
  "suggested_fix": "...",
  "fix_code_snippet": "...",
  "confidence_score": 0.0-1.0,
  "severity": "critical|high|medium|low",
  "failure_category": "...",
  "prevention_tips": ["..."],
  "is_flaky": true/false
}
Return ONLY valid JSON."""

        user = f"""Analyze this MUnit test failure:

Test Name: {test_name}
Error Message: {error_message}

Stack Trace:
{stack_trace[:3000]}

Mule Flow XML:
{flow_xml[:2000]}

MUnit Test XML:
{munit_xml[:2000]}"""

        logger.info("analyzing_failure", test=test_name)
        raw = await self._chat(system, user, temperature=0.05)

        try:
            # Extract JSON from response
            json_match = raw.strip()
            if "```json" in json_match:
                json_match = json_match.split("```json")[1].split("```")[0].strip()
            elif "```" in json_match:
                json_match = json_match.split("```")[1].split("```")[0].strip()
            return json.loads(json_match)
        except json.JSONDecodeError:
            return {
                "root_cause": raw[:500],
                "suggested_fix": "Manual investigation required",
                "fix_code_snippet": "",
                "confidence_score": 0.3,
                "severity": "medium",
                "failure_category": "unknown",
                "prevention_tips": [],
                "is_flaky": False,
            }

    async def generate_executive_summary(
        self,
        metrics: dict[str, Any],
        applications: list[dict],
    ) -> str:
        """Generate executive narrative for the dashboard report."""
        system = """You are a VP of Engineering writing an executive technology report.
Write in clear, business-focused language. Highlight risks, achievements, and recommendations.
Be concise but comprehensive. Use data to support all statements."""

        user = f"""Generate an executive summary for the AI-MUnit-Factory platform report.

Platform Metrics:
{json.dumps(metrics, indent=2)}

Application Summary (sample of {len(applications)} apps):
{json.dumps(applications[:5], indent=2)}

Write a 3-paragraph executive summary covering:
1. Current testing posture and coverage achievements
2. Risk areas requiring attention
3. Recommendations and next steps"""

        return await self._chat(system, user, temperature=0.3)

    async def risk_analysis(
        self,
        application_name: str,
        source_version: str,
        target_version: str,
        connectors: list[str],
        dependencies: list[dict],
        java_version: str,
    ) -> dict[str, Any]:
        """Assess migration risk for a Mule application."""
        system = """You are a Principal MuleSoft Migration Architect.
Analyze migration risks and return a JSON object with these exact keys:
{
  "overall_risk": "low|medium|high|critical",
  "migration_readiness_score": 0-100,
  "estimated_effort_days": integer,
  "connector_risks": [{"connector": "...", "risk": "...", "action": "..."}],
  "java_version_risks": ["..."],
  "policy_risks": ["..."],
  "dependency_risks": [{"artifact": "...", "issue": "...", "fix": "..."}],
  "breaking_changes": ["..."],
  "migration_plan": "...",
  "recommended_approach": "...",
  "rollback_strategy": "..."
}
Return ONLY valid JSON."""

        user = f"""Assess migration risk for this MuleSoft application:

Application: {application_name}
Current Mule Version: {source_version}
Target Mule Version: {target_version}
Java Version: {java_version}
Connectors: {', '.join(connectors)}

Dependencies (key ones):
{json.dumps(dependencies[:10], indent=2)}

Analyze risks for:
1. Connector compatibility between {source_version} → {target_version}
2. Java 8/11 → Java 17 migration issues
3. Policy enforcement changes
4. API Gateway behavior changes
5. Breaking connector version changes"""

        logger.info("risk_analysis", app=application_name, target=target_version)
        raw = await self._chat(system, user, temperature=0.05)

        try:
            json_match = raw.strip()
            if "```json" in json_match:
                json_match = json_match.split("```json")[1].split("```")[0].strip()
            elif "```" in json_match:
                json_match = json_match.split("```")[1].split("```")[0].strip()
            return json.loads(json_match)
        except json.JSONDecodeError:
            return {
                "overall_risk": "medium",
                "migration_readiness_score": 50,
                "estimated_effort_days": 5,
                "connector_risks": [],
                "java_version_risks": [],
                "policy_risks": [],
                "dependency_risks": [],
                "breaking_changes": [],
                "migration_plan": raw[:1000],
                "recommended_approach": "Manual review required",
                "rollback_strategy": "Blue-green deployment",
            }

    async def document_flow(self, flow_name: str, flow_xml: str) -> str:
        """Generate natural-language documentation for a Mule flow."""
        system = """You are a MuleSoft Solutions Architect documenting integration flows.
Write clear, technical documentation suitable for a developer wiki.
Cover: purpose, inputs, outputs, connectors used, error handling, business logic."""

        user = f"""Document this Mule 4 flow:

Flow Name: {flow_name}

Flow XML:
{flow_xml[:3000]}

Write 2-3 paragraphs of documentation."""

        return await self._chat(system, user, temperature=0.4)

    async def generate_coverage_recommendations(
        self,
        uncovered_flows: list[str],
        uncovered_processors: list[str],
        current_coverage: float,
    ) -> str:
        """Recommend tests to improve coverage."""
        system = """You are a QA Automation Architect specializing in MuleSoft testing.
Provide specific, actionable recommendations to improve MUnit coverage."""

        user = f"""Current coverage: {current_coverage:.1f}%

Uncovered flows: {', '.join(uncovered_flows[:20])}
Uncovered processors: {', '.join(uncovered_processors[:20])}

Provide specific recommendations to reach 95%+ coverage.
Prioritize by business risk and test value."""

        return await self._chat(system, user, temperature=0.3)
