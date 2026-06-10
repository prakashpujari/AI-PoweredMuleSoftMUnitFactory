"""pom.xml parser — extracts Mule runtime version, plugins, and dependencies."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import xmltodict

from app.utils.exceptions import ParseError
from app.utils.logging import get_logger

logger = get_logger(__name__)

MULE_NAMESPACES = {
    "http://www.mulesoft.com/schema/mule/core",
    "http://www.w3.org/2001/XMLSchema-instance",
}


class PomMetadata:
    """Structured result from pom.xml parsing."""

    def __init__(self) -> None:
        self.group_id: str = ""
        self.artifact_id: str = ""
        self.version: str = ""
        self.packaging: str = ""
        self.mule_runtime_version: str = ""
        self.java_version: str = ""
        self.mule_plugins: list[dict[str, str]] = []
        self.dependencies: list[dict[str, str]] = []
        self.connectors: list[dict[str, str]] = []
        self.properties: dict[str, str] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "artifact_id": self.artifact_id,
            "version": self.version,
            "packaging": self.packaging,
            "mule_runtime_version": self.mule_runtime_version,
            "java_version": self.java_version,
            "mule_plugins": self.mule_plugins,
            "dependencies": self.dependencies,
            "connectors": self.connectors,
            "properties": self.properties,
        }


class PomParser:
    """Parse Apache Maven pom.xml files for Mule application metadata."""

    MULE_CONNECTOR_GROUP_IDS = {
        "com.mulesoft.connectors",
        "org.mule.connectors",
        "com.mulesoft.munit",
        "org.mule.modules",
    }

    def parse_file(self, path: str | Path) -> PomMetadata:
        path = Path(path)
        if not path.exists():
            raise ParseError(f"pom.xml not found: {path}")
        try:
            content = path.read_text(encoding="utf-8")
            return self.parse_content(content)
        except Exception as e:
            raise ParseError(f"Failed to parse {path}: {e}", details=str(e))

    def parse_content(self, xml_content: str) -> PomMetadata:
        try:
            data = xmltodict.parse(xml_content, force_list=("dependency", "plugin"))
        except Exception as e:
            raise ParseError(f"Invalid XML: {e}")

        meta = PomMetadata()
        project = data.get("project", {})

        meta.group_id = project.get("groupId", "")
        meta.artifact_id = project.get("artifactId", "")
        meta.version = project.get("version", "")
        meta.packaging = project.get("packaging", "jar")

        # Properties
        props = project.get("properties", {}) or {}
        meta.properties = {k: str(v) for k, v in props.items() if v is not None}

        # Mule runtime version from app.runtime or mule.version property
        meta.mule_runtime_version = (
            meta.properties.get("app.runtime")
            or meta.properties.get("mule.version")
            or self._extract_runtime_from_plugins(project)
            or ""
        )
        meta.java_version = meta.properties.get("java.version", "")

        # Dependencies
        deps_node = project.get("dependencies", {}) or {}
        raw_deps = deps_node.get("dependency", []) if isinstance(deps_node, dict) else []
        for dep in raw_deps:
            if not isinstance(dep, dict):
                continue
            entry = {
                "group_id": dep.get("groupId", ""),
                "artifact_id": dep.get("artifactId", ""),
                "version": dep.get("version", ""),
                "classifier": dep.get("classifier", ""),
                "scope": dep.get("scope", "compile"),
            }
            meta.dependencies.append(entry)
            if entry["group_id"] in self.MULE_CONNECTOR_GROUP_IDS:
                meta.connectors.append(entry)

        # Plugins
        build = project.get("build", {}) or {}
        plugins_node = build.get("plugins", {}) or {}
        raw_plugins = plugins_node.get("plugin", []) if isinstance(plugins_node, dict) else []
        for plugin in raw_plugins:
            if not isinstance(plugin, dict):
                continue
            entry = {
                "group_id": plugin.get("groupId", ""),
                "artifact_id": plugin.get("artifactId", ""),
                "version": plugin.get("version", ""),
            }
            meta.mule_plugins.append(entry)

        logger.info(
            "pom_parsed",
            artifact=f"{meta.group_id}:{meta.artifact_id}:{meta.version}",
            runtime=meta.mule_runtime_version,
            connectors=len(meta.connectors),
        )
        return meta

    def _extract_runtime_from_plugins(self, project: dict) -> str:
        build = project.get("build", {}) or {}
        plugins_node = build.get("plugins", {}) or {}
        plugins = plugins_node.get("plugin", []) if isinstance(plugins_node, dict) else []
        for plugin in plugins:
            if not isinstance(plugin, dict):
                continue
            if "mule-maven-plugin" in plugin.get("artifactId", ""):
                config = plugin.get("configuration", {}) or {}
                runtime = config.get("runtimeVersion", "") or config.get("muleVersion", "")
                if runtime:
                    return runtime
        return ""
