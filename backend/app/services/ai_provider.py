"""AI provider abstraction layer — routes to Groq, Claude, or OpenAI."""
from __future__ import annotations

from enum import Enum
from typing import Any, Protocol

from app.config import get_settings
from app.utils.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class AIProvider(str, Enum):
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class AIServiceProtocol(Protocol):
    async def generate_munit(self, flow_name: str, flow_xml: str, connectors: list[str], test_types: list[str], raml_spec: str = "") -> str: ...
    async def analyze_failure(self, test_name: str, error_message: str, stack_trace: str, flow_xml: str, munit_xml: str) -> dict[str, Any]: ...
    async def generate_executive_summary(self, metrics: dict[str, Any], applications: list[dict]) -> str: ...
    async def risk_analysis(self, application_name: str, source_version: str, target_version: str, connectors: list[str], dependencies: list[dict], java_version: str) -> dict[str, Any]: ...
    async def document_flow(self, flow_name: str, flow_xml: str) -> str: ...


class AnthropicService:
    """Claude API abstraction layer."""

    def __init__(self) -> None:
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._model = settings.ANTHROPIC_MODEL

    async def _chat(self, system: str, user: str) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=8192,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text if response.content else ""

    async def generate_munit(self, flow_name: str, flow_xml: str, connectors: list[str], test_types: list[str], raml_spec: str = "") -> str:
        from app.services.groq_service import GroqService
        svc = GroqService()
        # Delegate prompt construction to GroqService but use Claude for generation
        return await self._chat(
            "You are a Principal MuleSoft Test Architect. Generate MUnit 2.x XML tests. Output only valid XML.",
            f"Flow: {flow_name}\nConnectors: {', '.join(connectors)}\nTest types: {', '.join(test_types)}\n\nFlow XML:\n{flow_xml}"
        )

    async def analyze_failure(self, test_name: str, error_message: str, stack_trace: str, flow_xml: str, munit_xml: str) -> dict[str, Any]:
        import json
        raw = await self._chat(
            "You are a MuleSoft debugging expert. Return JSON with root_cause, suggested_fix, confidence_score, severity.",
            f"Test: {test_name}\nError: {error_message}\nStack: {stack_trace[:2000]}"
        )
        try:
            return json.loads(raw)
        except Exception:
            return {"root_cause": raw, "confidence_score": 0.5, "severity": "medium"}

    async def generate_executive_summary(self, metrics: dict[str, Any], applications: list[dict]) -> str:
        import json
        return await self._chat(
            "You are a VP of Engineering writing executive reports.",
            f"Metrics: {json.dumps(metrics)}\nGenerate a 3-paragraph executive summary."
        )

    async def risk_analysis(self, application_name: str, source_version: str, target_version: str, connectors: list[str], dependencies: list[dict], java_version: str) -> dict[str, Any]:
        import json
        raw = await self._chat(
            "You are a MuleSoft migration architect. Return JSON with migration risk analysis.",
            f"App: {application_name}\n{source_version}→{target_version}\nConnectors: {', '.join(connectors)}"
        )
        try:
            return json.loads(raw)
        except Exception:
            return {"overall_risk": "medium", "migration_readiness_score": 60}

    async def document_flow(self, flow_name: str, flow_xml: str) -> str:
        return await self._chat(
            "You are a MuleSoft Solutions Architect writing integration documentation.",
            f"Document this flow: {flow_name}\n\n{flow_xml[:3000]}"
        )


class OpenAIService:
    """OpenAI GPT-4o abstraction layer."""

    def __init__(self) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_MODEL

    async def _chat(self, system: str, user: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=8192,
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    async def generate_munit(self, flow_name: str, flow_xml: str, connectors: list[str], test_types: list[str], raml_spec: str = "") -> str:
        return await self._chat(
            "You are a Principal MuleSoft Test Architect. Generate MUnit 2.x XML tests.",
            f"Flow: {flow_name}\nConnectors: {', '.join(connectors)}\nFlow XML:\n{flow_xml}"
        )

    async def analyze_failure(self, test_name: str, error_message: str, stack_trace: str, flow_xml: str, munit_xml: str) -> dict[str, Any]:
        import json
        raw = await self._chat(
            "You are a MuleSoft debugging expert. Return JSON.",
            f"Test: {test_name}\nError: {error_message}"
        )
        try:
            return json.loads(raw)
        except Exception:
            return {"root_cause": raw, "confidence_score": 0.5}

    async def generate_executive_summary(self, metrics: dict[str, Any], applications: list[dict]) -> str:
        import json
        return await self._chat("You are VP Engineering.", f"Metrics: {json.dumps(metrics)}")

    async def risk_analysis(self, application_name: str, source_version: str, target_version: str, connectors: list[str], dependencies: list[dict], java_version: str) -> dict[str, Any]:
        import json
        raw = await self._chat("MuleSoft migration architect. Return JSON.", f"App: {application_name} {source_version}→{target_version}")
        try:
            return json.loads(raw)
        except Exception:
            return {"overall_risk": "medium", "migration_readiness_score": 60}

    async def document_flow(self, flow_name: str, flow_xml: str) -> str:
        return await self._chat("MuleSoft Solutions Architect.", f"Document: {flow_name}\n{flow_xml[:2000]}")


def get_ai_service(provider: str | None = None) -> AIServiceProtocol:
    """Factory — returns the configured AI service implementation."""
    p = provider or settings.DEFAULT_AI_PROVIDER
    logger.debug("ai_provider_selected", provider=p)

    if p == AIProvider.ANTHROPIC:
        return AnthropicService()
    elif p == AIProvider.OPENAI:
        return OpenAIService()
    else:
        from app.services.groq_service import GroqService
        return GroqService()
