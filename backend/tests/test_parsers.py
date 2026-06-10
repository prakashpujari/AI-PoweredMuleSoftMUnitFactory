"""Unit tests for pom.xml, Mule XML, and RAML parsers."""
import pytest
from app.parsers.pom_parser import PomParser
from app.parsers.mule_xml_parser import MuleXmlParser
from app.parsers.raml_parser import RamlParser
from app.utils.exceptions import ParseError

# ── Sample fixtures ────────────────────────────────────────────────────────

SAMPLE_POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>order-api</artifactId>
    <version>1.2.0</version>
    <packaging>mule-application</packaging>
    <properties>
        <app.runtime>4.6.0</app.runtime>
        <java.version>11</java.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>com.mulesoft.connectors</groupId>
            <artifactId>mule-http-connector</artifactId>
            <version>1.8.4</version>
            <classifier>mule-plugin</classifier>
        </dependency>
        <dependency>
            <groupId>com.mulesoft.connectors</groupId>
            <artifactId>mule-db-connector</artifactId>
            <version>1.14.0</version>
            <classifier>mule-plugin</classifier>
        </dependency>
    </dependencies>
</project>"""

SAMPLE_MULE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<mule xmlns="http://www.mulesoft.org/schema/mule/core"
      xmlns:http="http://www.mulesoft.org/schema/mule/http"
      xmlns:db="http://www.mulesoft.org/schema/mule/db"
      xmlns:ee="http://www.mulesoft.org/schema/mule/ee/core">
    <flow name="get-orders-flow">
        <http:listener config-ref="HTTP_Listener_Config" path="/api/orders" />
        <db:select config-ref="Database_Config">
            <db:sql>SELECT * FROM orders</db:sql>
        </db:select>
        <ee:transform>
            <ee:message>
                <ee:set-payload><![CDATA[%dw 2.0 output application/json --- payload]]></ee:set-payload>
            </ee:message>
        </ee:transform>
        <error-handler>
            <on-error-propagate type="DB:CONNECTIVITY">
                <set-payload value="Database error" />
            </on-error-propagate>
        </error-handler>
    </flow>
    <sub-flow name="validate-order-subflow">
        <set-variable variableName="isValid" value="true" />
    </sub-flow>
</mule>"""

SAMPLE_RAML = """#%RAML 1.0
title: Order Management API
version: v1
baseUri: https://api.example.com/{version}
mediaType: application/json

/orders:
  displayName: Orders
  get:
    description: List all orders
    responses:
      200:
        body:
          application/json:
            example: |
              [{"id": "1", "status": "pending"}]
  post:
    description: Create order
    body:
      application/json:
        type: object
    responses:
      201:
        body:
          application/json:
  /{orderId}:
    get:
      description: Get order by ID
      responses:
        200:
"""


# ── PomParser tests ────────────────────────────────────────────────────────

class TestPomParser:
    def setup_method(self):
        self.parser = PomParser()

    def test_parse_group_id(self):
        meta = self.parser.parse_content(SAMPLE_POM)
        assert meta.group_id == "com.example"

    def test_parse_artifact_id(self):
        meta = self.parser.parse_content(SAMPLE_POM)
        assert meta.artifact_id == "order-api"

    def test_parse_version(self):
        meta = self.parser.parse_content(SAMPLE_POM)
        assert meta.version == "1.2.0"

    def test_parse_runtime_version(self):
        meta = self.parser.parse_content(SAMPLE_POM)
        assert meta.mule_runtime_version == "4.6.0"

    def test_parse_java_version(self):
        meta = self.parser.parse_content(SAMPLE_POM)
        assert meta.java_version == "11"

    def test_parse_connectors(self):
        meta = self.parser.parse_content(SAMPLE_POM)
        assert len(meta.connectors) == 2
        connector_ids = [c["artifact_id"] for c in meta.connectors]
        assert "mule-http-connector" in connector_ids
        assert "mule-db-connector" in connector_ids

    def test_parse_dependencies_count(self):
        meta = self.parser.parse_content(SAMPLE_POM)
        assert len(meta.dependencies) == 2

    def test_to_dict_returns_dict(self):
        meta = self.parser.parse_content(SAMPLE_POM)
        d = meta.to_dict()
        assert isinstance(d, dict)
        assert "group_id" in d
        assert "mule_runtime_version" in d

    def test_invalid_xml_raises_parse_error(self):
        with pytest.raises(ParseError):
            self.parser.parse_content("<invalid xml>")


# ── MuleXmlParser tests ────────────────────────────────────────────────────

class TestMuleXmlParser:
    def setup_method(self):
        self.parser = MuleXmlParser()

    def test_parse_flows_count(self):
        flows = self.parser.parse_content(SAMPLE_MULE_XML.encode())
        assert len(flows) == 2

    def test_parse_flow_name(self):
        flows = self.parser.parse_content(SAMPLE_MULE_XML.encode())
        names = [f.name for f in flows]
        assert "get-orders-flow" in names

    def test_parse_subflow(self):
        flows = self.parser.parse_content(SAMPLE_MULE_XML.encode())
        subflows = [f for f in flows if f.flow_type == "subflow"]
        assert len(subflows) == 1
        assert subflows[0].name == "validate-order-subflow"

    def test_parse_connectors(self):
        flows = self.parser.parse_content(SAMPLE_MULE_XML.encode())
        main_flow = next(f for f in flows if f.name == "get-orders-flow")
        assert "http" in main_flow.connectors_used
        assert "database" in main_flow.connectors_used

    def test_parse_error_handler(self):
        flows = self.parser.parse_content(SAMPLE_MULE_XML.encode())
        main_flow = next(f for f in flows if f.name == "get-orders-flow")
        assert main_flow.has_error_handler is True

    def test_parse_dataweave(self):
        flows = self.parser.parse_content(SAMPLE_MULE_XML.encode())
        main_flow = next(f for f in flows if f.name == "get-orders-flow")
        assert main_flow.has_dataweave is True

    def test_parse_variables(self):
        flows = self.parser.parse_content(SAMPLE_MULE_XML.encode())
        subflow = next(f for f in flows if f.name == "validate-order-subflow")
        assert "isValid" in subflow.variables

    def test_to_dict_complete(self):
        flows = self.parser.parse_content(SAMPLE_MULE_XML.encode())
        d = flows[0].to_dict()
        assert "name" in d
        assert "processors" in d
        assert "connectors_used" in d


# ── RamlParser tests ────────────────────────────────────────────────────────

class TestRamlParser:
    def setup_method(self):
        self.parser = RamlParser()

    def test_parse_title(self):
        spec = self.parser.parse_content(SAMPLE_RAML)
        assert spec.title == "Order Management API"

    def test_parse_version(self):
        spec = self.parser.parse_content(SAMPLE_RAML)
        assert spec.version == "v1"

    def test_parse_raml_version(self):
        spec = self.parser.parse_content(SAMPLE_RAML)
        assert spec.raml_version == "1.0"

    def test_parse_resources(self):
        spec = self.parser.parse_content(SAMPLE_RAML)
        assert len(spec.resources) == 1
        assert spec.resources[0].path == "/orders"

    def test_parse_methods(self):
        spec = self.parser.parse_content(SAMPLE_RAML)
        orders = spec.resources[0]
        methods = [m.method for m in orders.methods]
        assert "GET" in methods
        assert "POST" in methods

    def test_parse_nested_resources(self):
        spec = self.parser.parse_content(SAMPLE_RAML)
        orders = spec.resources[0]
        assert len(orders.sub_resources) == 1
        assert orders.sub_resources[0].path == "/orders/{orderId}"

    def test_to_dict(self):
        spec = self.parser.parse_content(SAMPLE_RAML)
        d = spec.to_dict()
        assert d["title"] == "Order Management API"
        assert d["resources"][0]["path"] == "/orders"
