"""Agent 7 — Migration Agent: assesses Mule 4.x → 4.9 migration risks."""
from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph, END

from app.agents.base_agent import AgentState, BaseAgent
from app.services.ai_provider import get_ai_service
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Known breaking changes by version transition
KNOWN_BREAKING_CHANGES = {
    "4.4_to_4.9": [
        "HTTP Connector 1.x → 1.8: TLS 1.0/1.1 deprecated",
        "DataWeave 2.4 → 2.7: some transformation functions renamed",
        "MUnit 2.3 → 3.1: test suite XML schema changes",
        "Anypoint MQ 2.x → 4.x: configuration changes required",
        "Salesforce Connector 10.x → 16.x: API version upgrade needed",
    ],
    "4.6_to_4.9": [
        "Java 8/11 → Java 17: java.* API removals",
        "Spring Security updates: javax → jakarta namespace",
        "Database Connector 1.13 → 1.14: connection pool changes",
        "ObjectStore Connector 1.x → 2.x: configuration migration",
    ],
}

CONNECTOR_VERSION_RISKS = {
    "salesforce": "Major version upgrade likely required. Check SOQL/SOSL compatibility.",
    "database": "Connection pool configuration may change. Test with target DB drivers.",
    "http": "TLS settings review required. Certificate validation stricter.",
    "kafka": "Consumer group configurations may need update.",
    "jms": "Message acknowledgement behavior changes in newer versions.",
    "sftp": "Authentication mechanism changes possible.",
}


class MigrationAgent(BaseAgent):
    name = "migration_agent"

    def _build_graph(self) -> Any:
        graph = StateGraph(AgentState)
        graph.add_node("identify_source_version", self._identify_source_version)
        graph.add_node("check_connector_compatibility", self._check_connector_compatibility)
        graph.add_node("check_java_compatibility", self._check_java_compatibility)
        graph.add_node("check_policy_risks", self._check_policy_risks)
        graph.add_node("ai_risk_assessment", self._ai_risk_assessment)
        graph.add_node("build_migration_report", self._build_migration_report)

        graph.set_entry_point("identify_source_version")
        graph.add_edge("identify_source_version", "check_connector_compatibility")
        graph.add_edge("check_connector_compatibility", "check_java_compatibility")
        graph.add_edge("check_java_compatibility", "check_policy_risks")
        graph.add_edge("check_policy_risks", "ai_risk_assessment")
        graph.add_edge("ai_risk_assessment", "build_migration_report")
        graph.add_edge("build_migration_report", END)

        return graph.compile()

    async def _identify_source_version(self, state: AgentState) -> AgentState:
        state["current_step"] = "identify_source_version"
        pom = state.get("pom_metadata", {})
        cfg = state.get("config", {})

        source_version = pom.get("mule_runtime_version", "") or cfg.get("source_version", "4.4.0")
        target_version = cfg.get("target_version", "4.9.0")

        state.setdefault("migration_context", {})
        state["migration_context"]["source_version"] = source_version
        state["migration_context"]["target_version"] = target_version
        state["migration_context"]["java_version"] = pom.get("java_version", "11")

        logger.info("migration_versions", source=source_version, target=target_version)
        return state

    async def _check_connector_compatibility(self, state: AgentState) -> AgentState:
        state["current_step"] = "check_connector_compatibility"
        pom = state.get("pom_metadata", {})
        connectors_in_use = [c.get("artifact_id", "") for c in pom.get("connectors", [])]

        connector_risks = []
        for connector_artifact in connectors_in_use:
            for key, risk_desc in CONNECTOR_VERSION_RISKS.items():
                if key in connector_artifact.lower():
                    connector_risks.append({
                        "connector": connector_artifact,
                        "risk": risk_desc,
                        "action": f"Review {connector_artifact} changelog for target version",
                        "severity": "medium",
                    })

        state["migration_context"]["connector_risks"] = connector_risks
        logger.info("connector_risks_identified", count=len(connector_risks))
        return state

    async def _check_java_compatibility(self, state: AgentState) -> AgentState:
        state["current_step"] = "check_java_compatibility"
        java_version = state.get("migration_context", {}).get("java_version", "11")
        target_version = state.get("migration_context", {}).get("target_version", "4.9.0")

        java_risks = []
        if java_version in ("8", "11") and target_version >= "4.7":
            java_risks = [
                "Java 17 required for Mule 4.7+: review javax vs jakarta namespace changes",
                "Removed Java reflection APIs: audit custom Java components",
                "SecurityManager deprecated: review policy configurations",
                "Nashorn JavaScript engine removed: update DataWeave scripts using Java interop",
            ]

        state["migration_context"]["java_version_risks"] = java_risks
        return state

    async def _check_policy_risks(self, state: AgentState) -> AgentState:
        state["current_step"] = "check_policy_risks"
        raml_spec = state.get("raml_spec", {})
        security_schemes = raml_spec.get("security_schemes", [])

        policy_risks = []
        for scheme in security_schemes:
            if "oauth" in str(scheme).lower():
                policy_risks.append("OAuth 2.0 policy: verify token validation endpoint compatibility")
            if "jwt" in str(scheme).lower():
                policy_risks.append("JWT policy: check algorithm support in target Anypoint version")
            if "client" in str(scheme).lower():
                policy_risks.append("Client ID Enforcement: review policy version compatibility")

        state["migration_context"]["policy_risks"] = policy_risks
        return state

    async def _ai_risk_assessment(self, state: AgentState) -> AgentState:
        state["current_step"] = "ai_risk_assessment"
        ctx = state.get("migration_context", {})
        pom = state.get("pom_metadata", {})
        app_meta = state.get("app_metadata", {})

        try:
            ai_service = get_ai_service()
            assessment = await ai_service.risk_analysis(
                application_name=app_meta.get("name", "unknown"),
                source_version=ctx.get("source_version", ""),
                target_version=ctx.get("target_version", ""),
                connectors=app_meta.get("connectors", []),
                dependencies=pom.get("dependencies", []),
                java_version=ctx.get("java_version", "11"),
            )
            state["migration_context"]["ai_assessment"] = assessment
        except Exception as e:
            logger.warning("ai_risk_assessment_error", error=str(e))
            state["migration_context"]["ai_assessment"] = {
                "overall_risk": "medium",
                "migration_readiness_score": 60,
                "migration_plan": "Manual assessment required",
            }

        return state

    async def _build_migration_report(self, state: AgentState) -> AgentState:
        state["current_step"] = "build_migration_report"
        ctx = state.get("migration_context", {})
        ai = ctx.get("ai_assessment", {})

        source = ctx.get("source_version", "")
        target = ctx.get("target_version", "")

        # Version transition key
        major_minor = lambda v: ".".join(v.split(".")[:2])
        transition_key = f"{major_minor(source).replace('.', '_')}_to_{major_minor(target).replace('.', '_')}"
        known_changes = KNOWN_BREAKING_CHANGES.get(transition_key, [])

        all_connector_risks = ctx.get("connector_risks", []) + ai.get("connector_risks", [])
        all_java_risks = ctx.get("java_version_risks", []) + ai.get("java_version_risks", [])
        all_policy_risks = ctx.get("policy_risks", []) + ai.get("policy_risks", [])
        breaking_changes = known_changes + ai.get("breaking_changes", [])

        risk_level = ai.get("overall_risk", "medium")
        readiness_score = float(ai.get("migration_readiness_score", 60))

        state["migration_report"] = {
            "source_version": source,
            "target_version": target,
            "overall_risk": risk_level,
            "migration_readiness_score": readiness_score,
            "estimated_effort_days": ai.get("estimated_effort_days", 5),
            "connector_risks": all_connector_risks,
            "java_version_risks": all_java_risks,
            "policy_risks": all_policy_risks,
            "breaking_changes": breaking_changes,
            "migration_plan": ai.get("migration_plan", ""),
            "recommended_approach": ai.get("recommended_approach", "Blue-green deployment"),
            "rollback_strategy": ai.get("rollback_strategy", "Keep previous version deployed"),
            "risk_count_critical": len([r for r in all_connector_risks if r.get("severity") == "critical"]),
            "risk_count_high": len([r for r in all_connector_risks if r.get("severity") == "high"]),
            "risk_count_medium": len([r for r in all_connector_risks if r.get("severity") == "medium"]),
        }

        logger.info(
            "migration_report_built",
            risk=risk_level,
            readiness=readiness_score,
            breaking_changes=len(breaking_changes),
        )
        return state
