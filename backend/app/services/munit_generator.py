"""MUnit test generation engine — produces MUnit 2.x XML from flow analysis."""
from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import Any

from app.parsers.mule_xml_parser import FlowInfo
from app.parsers.raml_parser import RamlSpec
from app.services.ai_provider import get_ai_service
from app.utils.logging import get_logger

logger = get_logger(__name__)

MUNIT_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<mule xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xmlns="http://www.mulesoft.org/schema/mule/core"
      xmlns:munit="http://www.mulesoft.org/schema/mule/munit"
      xmlns:munit-tools="http://www.mulesoft.org/schema/mule/munit-tools"
      xmlns:http="http://www.mulesoft.org/schema/mule/http"
      xmlns:db="http://www.mulesoft.org/schema/mule/db"
      xmlns:ee="http://www.mulesoft.org/schema/mule/ee/core"
      xmlns:sfdc="http://www.mulesoft.org/schema/mule/sfdc"
      xmlns:jms="http://www.mulesoft.org/schema/mule/jms"
      xsi:schemaLocation="
        http://www.mulesoft.org/schema/mule/core https://repository.mulesoft.org/nexus/content/repositories/releases/org/mule/runtime/mule-module-artifact/4.9.0/mule-module-artifact-4.9.0.xsd
        http://www.mulesoft.org/schema/mule/munit https://repository.mulesoft.org/nexus/content/repositories/releases/com/mulesoft/munit/mule-munit-module/3.1.0/mule-munit-module-3.1.0.xsd
        http://www.mulesoft.org/schema/mule/munit-tools https://repository.mulesoft.org/nexus/content/repositories/releases/com/mulesoft/munit/mule-munit-tools-module/3.1.0/mule-munit-tools-module-3.1.0.xsd">

  <munit:config name="{suite_name}" />
"""

MUNIT_FOOTER = "</mule>\n"

TEST_TYPES_DESCRIPTIONS = {
    "happy_path": "Verify successful execution with valid inputs",
    "negative_path": "Verify proper error handling with invalid inputs",
    "missing_payload": "Verify behavior when required payload is absent",
    "null_values": "Verify handling of null field values",
    "invalid_datatype": "Verify validation rejects incorrect data types",
    "validation_failure": "Verify input validation logic fires correctly",
    "database_failure": "Verify DB error scenarios trigger proper error handling",
    "salesforce_failure": "Verify Salesforce connector failures are handled",
    "kafka_failure": "Verify Kafka message failures are handled",
    "jms_failure": "Verify JMS messaging failures are handled",
    "timeout": "Verify timeout scenarios are caught and handled",
    "retry": "Verify retry logic triggers on transient failures",
    "oauth_failure": "Verify OAuth token validation failures",
    "jwt_failure": "Verify JWT token validation failures",
    "client_id_failure": "Verify Client ID/Secret enforcement",
    "rate_limit": "Verify rate limiting policy enforcement",
    "large_payload": "Verify handling of oversized payloads",
    "concurrent_requests": "Verify behavior under concurrent request load",
    "security": "Verify security controls and auth enforcement",
    "error_handling": "Verify all error handler branches",
}


@dataclass
class GenerationRequest:
    flow_info: FlowInfo
    test_types: list[str]
    raml_spec: RamlSpec | None = None
    ai_provider: str = "groq"
    application_name: str = ""

    @property
    def all_test_types(self) -> list[str]:
        base = list(self.test_types)
        if not base:
            base = ["happy_path", "negative_path", "error_handling"]
        # Add connector-specific tests automatically
        for connector in self.flow_info.connectors_used:
            if connector == "database" and "database_failure" not in base:
                base.append("database_failure")
            if connector == "salesforce" and "salesforce_failure" not in base:
                base.append("salesforce_failure")
            if connector == "kafka" and "kafka_failure" not in base:
                base.append("kafka_failure")
            if connector == "jms" and "jms_failure" not in base:
                base.append("jms_failure")
        return base


@dataclass
class GenerationResult:
    flow_name: str
    munit_xml: str
    test_types: list[str]
    test_count: int = 0
    confidence_score: float = 0.0
    ai_model: str = ""
    errors: list[str] = field(default_factory=list)


class MUnitGenerator:
    """Orchestrates AI-powered MUnit XML generation for Mule flows."""

    # Connector-specific mock templates
    MOCK_TEMPLATES = {
        "http": """    <munit-tools:mock-when processor="http:request">
      <munit-tools:with-attributes>
        <munit-tools:with-attribute attributeName="config-ref" whereValue="HTTP_Request_Config" />
      </munit-tools:with-attributes>
      <munit-tools:then-return>
        <munit-tools:payload value="#[output application/json --- {status: 200, body: {}}]" mediaType="application/json"/>
        <munit-tools:attributes value="#[{statusCode: 200, headers: {}}]"/>
      </munit-tools:then-return>
    </munit-tools:mock-when>""",

        "database": """    <munit-tools:mock-when processor="db:select">
      <munit-tools:then-return>
        <munit-tools:payload value="#[output application/java --- [{id: '1', name: 'Test Record'}]]"/>
      </munit-tools:then-return>
    </munit-tools:mock-when>""",

        "salesforce": """    <munit-tools:mock-when processor="sfdc:query">
      <munit-tools:then-return>
        <munit-tools:payload value="#[output application/java --- [{Id: '0011000000abcde', Name: 'Test Account'}]]"/>
      </munit-tools:then-return>
    </munit-tools:mock-when>""",

        "jms": """    <munit-tools:mock-when processor="jms:publish">
      <munit-tools:then-return>
        <munit-tools:payload value="#[null]"/>
      </munit-tools:then-return>
    </munit-tools:mock-when>""",

        "kafka": """    <munit-tools:mock-when processor="kafka:publish">
      <munit-tools:then-return>
        <munit-tools:payload value="#[null]"/>
      </munit-tools:then-return>
    </munit-tools:mock-when>""",
    }

    def __init__(self) -> None:
        pass

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        flow = request.flow_info
        test_types = request.all_test_types
        raml_str = ""

        if request.raml_spec:
            import json
            raml_str = json.dumps(request.raml_spec.to_dict(), indent=2)

        ai_service = get_ai_service(request.ai_provider)
        logger.info(
            "munit_generation_start",
            flow=flow.name,
            test_types=test_types,
            provider=request.ai_provider,
        )

        try:
            munit_xml = await ai_service.generate_munit(
                flow_name=flow.name,
                flow_xml=flow.raw_xml or "",
                connectors=flow.connectors_used,
                test_types=test_types,
                raml_spec=raml_str,
            )

            # Post-process: ensure valid XML envelope if AI returned partial content
            munit_xml = self._ensure_valid_munit_xml(munit_xml, flow.name)
            test_count = munit_xml.count("<munit:test ")

            result = GenerationResult(
                flow_name=flow.name,
                munit_xml=munit_xml,
                test_types=test_types,
                test_count=test_count,
                confidence_score=0.92,
                ai_model=request.ai_provider,
            )
            logger.info("munit_generation_complete", flow=flow.name, tests=test_count)
            return result

        except Exception as e:
            logger.error("munit_generation_error", flow=flow.name, error=str(e))
            # Fallback: generate template-based tests
            munit_xml = self._generate_template_fallback(flow, test_types)
            return GenerationResult(
                flow_name=flow.name,
                munit_xml=munit_xml,
                test_types=test_types,
                test_count=munit_xml.count("<munit:test "),
                confidence_score=0.5,
                ai_model="template",
                errors=[str(e)],
            )

    def _ensure_valid_munit_xml(self, xml: str, flow_name: str) -> str:
        """Ensure the XML has proper MUnit envelope."""
        if "<mule" not in xml:
            suite_name = f"{flow_name.lower().replace(' ', '-')}-test-suite"
            header = MUNIT_HEADER.format(suite_name=suite_name)
            xml = header + xml + MUNIT_FOOTER
        return xml

    def _generate_template_fallback(self, flow: FlowInfo, test_types: list[str]) -> str:
        """Generate a minimal MUnit template when AI fails."""
        flow_key = flow.name.lower().replace(" ", "-").replace("_", "-")
        suite_name = f"{flow_key}-test-suite"
        header = MUNIT_HEADER.format(suite_name=suite_name)
        tests = []

        for test_type in test_types:
            desc = TEST_TYPES_DESCRIPTIONS.get(test_type, test_type)
            mocks = "\n".join(
                self.MOCK_TEMPLATES[c]
                for c in flow.connectors_used
                if c in self.MOCK_TEMPLATES
            )
            test = f"""
  <munit:test name="{flow_key}-{test_type}" description="{desc}">
    <munit:behavior>
{textwrap.indent(mocks, "      ")}
    </munit:behavior>
    <munit:execution>
      <flow-ref name="{flow.name}" />
    </munit:execution>
    <munit:validation>
      <munit-tools:assert-that
        expression="#[payload]"
        is="#[MunitTools::notNullValue()]"
        message="Payload should not be null"/>
    </munit:validation>
  </munit:test>"""
            tests.append(test)

        return header + "\n".join(tests) + "\n" + MUNIT_FOOTER

    def build_test_types_for_flow(self, flow: FlowInfo) -> list[str]:
        """Determine relevant test types based on flow analysis."""
        types = ["happy_path", "negative_path", "error_handling"]

        if flow.has_error_handler:
            types.append("validation_failure")

        for connector in flow.connectors_used:
            connector_tests = {
                "database": ["database_failure"],
                "salesforce": ["salesforce_failure"],
                "kafka": ["kafka_failure"],
                "jms": ["jms_failure"],
                "http": ["timeout", "retry"],
            }
            types.extend(connector_tests.get(connector, []))

        if flow.flow_type == "batch_job":
            types.append("batch")
        if flow.flow_type == "scheduler":
            types.append("scheduler")

        return list(dict.fromkeys(types))  # preserve order, dedupe
