"""Mule 4 XML config file parser — extracts flows, processors, connectors, DW scripts."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from lxml import etree

from app.utils.exceptions import ParseError
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Mule 4 XML namespaces
MULE_NS = "http://www.mulesoft.org/schema/mule/core"
HTTP_NS = "http://www.mulesoft.org/schema/mule/http"
DB_NS = "http://www.mulesoft.org/schema/mule/db"
SFDC_NS = "http://www.mulesoft.org/schema/mule/sfdc"
JMS_NS = "http://www.mulesoft.org/schema/mule/jms"
KAFKA_NS = "http://www.mulesoft.org/schema/mule/kafka"
SCHED_NS = "http://www.mulesoft.org/schema/mule/scheduler"
BATCH_NS = "http://www.mulesoft.org/schema/mule/batch"
EE_NS = "http://www.mulesoft.org/schema/mule/ee/core"
VM_NS = "http://www.mulesoft.org/schema/mule/vm"
AMQP_NS = "http://www.mulesoft.org/schema/mule/amqp"

CONNECTOR_NAMESPACES = {
    HTTP_NS: "http",
    DB_NS: "database",
    SFDC_NS: "salesforce",
    JMS_NS: "jms",
    KAFKA_NS: "kafka",
    SCHED_NS: "scheduler",
    BATCH_NS: "batch",
    VM_NS: "vm",
    AMQP_NS: "amqp",
    EE_NS: "dataweave",
}


class FlowInfo:
    def __init__(self) -> None:
        self.name: str = ""
        self.flow_type: str = "flow"
        self.processors: list[dict] = []
        self.connectors_used: list[str] = []
        self.error_handlers: list[dict] = []
        self.dataweave_scripts: list[str] = []
        self.variables: dict[str, str] = {}
        self.has_error_handler: bool = False
        self.has_dataweave: bool = False
        self.is_async: bool = False
        self.processor_count: int = 0
        self.raw_xml: str = ""
        self.source_file: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "flow_type": self.flow_type,
            "processors": self.processors,
            "connectors_used": self.connectors_used,
            "error_handlers": self.error_handlers,
            "dataweave_scripts": self.dataweave_scripts,
            "variables": self.variables,
            "has_error_handler": self.has_error_handler,
            "has_dataweave": self.has_dataweave,
            "is_async": self.is_async,
            "processor_count": self.processor_count,
            "source_file": self.source_file,
        }


class MuleXmlParser:
    """Parse Mule 4 XML configuration files into structured FlowInfo objects."""

    def parse_directory(self, src_dir: str | Path) -> list[FlowInfo]:
        src_path = Path(src_dir)
        flows: list[FlowInfo] = []
        xml_files = list(src_path.rglob("*.xml"))
        logger.info("scanning_xml_files", count=len(xml_files), path=str(src_path))

        for xml_file in xml_files:
            try:
                file_flows = self.parse_file(xml_file)
                for f in file_flows:
                    f.source_file = str(xml_file.relative_to(src_path))
                flows.extend(file_flows)
            except ParseError as e:
                logger.warning("xml_parse_skip", file=str(xml_file), error=str(e))

        logger.info("xml_parse_complete", flows_found=len(flows))
        return flows

    def parse_file(self, path: str | Path) -> list[FlowInfo]:
        path = Path(path)
        if not path.exists():
            raise ParseError(f"File not found: {path}")
        try:
            content = path.read_bytes()
            return self.parse_content(content, source_file=str(path))
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Failed to parse {path}: {e}")

    def parse_content(self, xml_bytes: bytes, source_file: str = "") -> list[FlowInfo]:
        try:
            root = etree.fromstring(xml_bytes)
        except etree.XMLSyntaxError as e:
            raise ParseError(f"XML syntax error: {e}")

        flows: list[FlowInfo] = []

        # Top-level flow elements
        for tag, flow_type in [
            (f"{{{MULE_NS}}}flow", "flow"),
            (f"{{{MULE_NS}}}sub-flow", "subflow"),
        ]:
            for elem in root.findall(tag):
                flow = self._extract_flow(elem, flow_type)
                flow.source_file = source_file
                flows.append(flow)

        # Batch jobs (top-level)
        for elem in root.findall(f"{{{BATCH_NS}}}job"):
            flow = self._extract_flow(elem, "batch_job")
            flow.source_file = source_file
            flows.append(flow)

        return flows

    def _extract_flow(self, elem: etree._Element, flow_type: str) -> FlowInfo:
        flow = FlowInfo()
        flow.name = elem.get("name", "unnamed")
        flow.flow_type = flow_type
        flow.is_async = elem.get("initialState", "") == "stopped"
        flow.raw_xml = etree.tostring(elem, encoding="unicode", pretty_print=True)

        connectors_seen: set[str] = set()

        for child in elem.iter():
            tag_local = etree.QName(child.tag).localname if child.tag != etree.Comment else None
            tag_ns = etree.QName(child.tag).namespace if child.tag != etree.Comment else None

            if tag_local is None:
                continue

            # Map namespace to connector type
            connector_type = CONNECTOR_NAMESPACES.get(tag_ns)
            if connector_type and connector_type != "dataweave":
                connectors_seen.add(connector_type)

            # Detect DataWeave
            if tag_ns == EE_NS and tag_local == "transform":
                flow.has_dataweave = True
                dw_body = child.find(f"{{{EE_NS}}}message/{{{EE_NS}}}set-payload")
                if dw_body is not None and dw_body.text:
                    flow.dataweave_scripts.append(dw_body.text.strip())

            # Capture set-variable
            if tag_ns == MULE_NS and tag_local == "set-variable":
                var_name = child.get("variableName", child.get("variable", ""))
                var_val = child.get("value", "")
                if var_name:
                    flow.variables[var_name] = var_val

            # Error handlers
            if tag_local in ("error-handler", "on-error-propagate", "on-error-continue"):
                flow.has_error_handler = True
                flow.error_handlers.append({"type": tag_local, "errors": child.get("type", "ANY")})

            # Count processors (direct children only)
            if child in elem:
                if tag_local not in ("error-handler",):
                    flow.processor_count += 1
                    flow.processors.append({
                        "tag": tag_local,
                        "namespace": tag_ns,
                        "connector": connector_type,
                        "attrs": dict(child.attrib),
                    })

        flow.connectors_used = sorted(connectors_seen)
        return flow
