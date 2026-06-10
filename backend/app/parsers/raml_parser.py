"""RAML 1.0 / 0.8 parser — extracts resources, methods, schemas, examples."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from ruamel.yaml import YAML

from app.utils.exceptions import ParseError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RamlResource:
    def __init__(self) -> None:
        self.path: str = ""
        self.display_name: str = ""
        self.description: str = ""
        self.methods: list[RamlMethod] = []
        self.uri_parameters: dict[str, Any] = {}
        self.sub_resources: list["RamlResource"] = []

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "display_name": self.display_name,
            "description": self.description,
            "methods": [m.to_dict() for m in self.methods],
            "uri_parameters": self.uri_parameters,
            "sub_resources": [r.to_dict() for r in self.sub_resources],
        }


class RamlMethod:
    def __init__(self) -> None:
        self.method: str = ""
        self.description: str = ""
        self.query_parameters: dict[str, Any] = {}
        self.request_body: dict[str, Any] = {}
        self.responses: dict[str, Any] = {}
        self.security_schemes: list[str] = []
        self.headers: dict[str, Any] = {}

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "description": self.description,
            "query_parameters": self.query_parameters,
            "request_body": self.request_body,
            "responses": self.responses,
            "security_schemes": self.security_schemes,
            "headers": self.headers,
        }


class RamlSpec:
    def __init__(self) -> None:
        self.title: str = ""
        self.version: str = ""
        self.base_uri: str = ""
        self.media_types: list[str] = []
        self.security_schemes: dict[str, Any] = {}
        self.types: dict[str, Any] = {}
        self.traits: dict[str, Any] = {}
        self.resources: list[RamlResource] = []
        self.raml_version: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "version": self.version,
            "base_uri": self.base_uri,
            "media_types": self.media_types,
            "security_schemes": list(self.security_schemes.keys()),
            "types_count": len(self.types),
            "resources": [r.to_dict() for r in self.resources],
            "raml_version": self.raml_version,
        }


class RamlParser:
    """Parse RAML specification files into structured RamlSpec objects."""

    HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}

    def parse_file(self, path: str | Path) -> RamlSpec:
        path = Path(path)
        if not path.exists():
            raise ParseError(f"RAML file not found: {path}")
        try:
            content = path.read_text(encoding="utf-8")
            return self.parse_content(content)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Failed to parse RAML {path}: {e}")

    def parse_content(self, content: str) -> RamlSpec:
        spec = RamlSpec()

        # Detect RAML version from header
        first_line = content.splitlines()[0] if content.strip() else ""
        if "#%RAML 1.0" in first_line:
            spec.raml_version = "1.0"
        elif "#%RAML 0.8" in first_line:
            spec.raml_version = "0.8"

        # Strip RAML comment header for YAML parsing
        yaml_content = "\n".join(
            line for line in content.splitlines()
            if not line.startswith("#%RAML")
        )

        try:
            ryaml = YAML()
            ryaml.preserve_quotes = True
            import io
            data = ryaml.load(io.StringIO(yaml_content)) or {}
        except Exception as e:
            raise ParseError(f"RAML YAML parse error: {e}")

        spec.title = str(data.get("title", ""))
        spec.version = str(data.get("version", ""))
        spec.base_uri = str(data.get("baseUri", ""))

        media = data.get("mediaType", [])
        spec.media_types = [media] if isinstance(media, str) else list(media or [])
        spec.security_schemes = dict(data.get("securitySchemes", {}) or {})
        spec.types = dict(data.get("types", {}) or {})
        spec.traits = dict(data.get("traits", {}) or {})

        # Parse top-level resources (keys starting with /)
        for key, value in data.items():
            if isinstance(key, str) and key.startswith("/"):
                resource = self._parse_resource(key, value or {})
                spec.resources.append(resource)

        logger.info(
            "raml_parsed",
            title=spec.title,
            version=spec.version,
            resources=len(spec.resources),
        )
        return spec

    def _parse_resource(self, path: str, data: dict) -> RamlResource:
        resource = RamlResource()
        resource.path = path
        resource.display_name = str(data.get("displayName", ""))
        resource.description = str(data.get("description", ""))
        resource.uri_parameters = dict(data.get("uriParameters", {}) or {})

        for method in self.HTTP_METHODS:
            if method in data:
                m = self._parse_method(method, data[method] or {})
                resource.methods.append(m)

        # Nested resources
        for key, value in data.items():
            if isinstance(key, str) and key.startswith("/"):
                sub = self._parse_resource(path + key, value or {})
                resource.sub_resources.append(sub)

        return resource

    def _parse_method(self, method: str, data: dict) -> RamlMethod:
        m = RamlMethod()
        m.method = method.upper()
        m.description = str(data.get("description", ""))
        m.query_parameters = dict(data.get("queryParameters", {}) or {})
        m.headers = dict(data.get("headers", {}) or {})

        body = data.get("body", {})
        if isinstance(body, dict):
            m.request_body = body

        responses = data.get("responses", {})
        if isinstance(responses, dict):
            m.responses = responses

        sec = data.get("securedBy", [])
        m.security_schemes = [str(s) for s in (sec or []) if s]

        return m
