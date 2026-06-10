# AI-MUnit-Factory — C4 Architecture Model

## Level 1: System Context

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           System Context                                 │
│                                                                          │
│   [MuleSoft Developer]         [QA Engineer]         [Architect/VP]     │
│         │                           │                       │           │
│         └─────────────────┬─────────┘                       │           │
│                           │                                 │           │
│               ┌───────────▼──────────────────────┐          │           │
│               │      AI-MUnit-Factory             │◄─────────┘           │
│               │  (This System)                    │                      │
│               └────────────┬─────────────────────┘                      │
│                            │                                             │
│         ┌──────────────────┼──────────────────────┐                    │
│         │                  │                       │                    │
│   ┌─────▼──────┐  ┌───────▼──────┐  ┌────────────▼──────────────┐    │
│   │  Groq API  │  │ Anypoint     │  │  GitHub Repositories       │    │
│   │  (LLM)     │  │ Platform     │  │  (Source Code)             │    │
│   └────────────┘  └──────────────┘  └───────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

## Level 2: Container Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        AI-MUnit-Factory Containers                       │
│                                                                          │
│  ┌────────────────────┐    ┌────────────────────┐                       │
│  │  React Frontend    │    │   FastAPI Backend   │                       │
│  │  (Port 3000/80)    │───►│   (Port 8000)       │                       │
│  │  TypeScript + MUI  │    │   Python 3.12       │                       │
│  └────────────────────┘    └──────────┬──────────┘                       │
│                                       │                                  │
│              ┌────────────────────────┤                                  │
│              │                        │                                  │
│  ┌───────────▼────────┐  ┌───────────▼────────┐  ┌──────────────────┐  │
│  │   LangGraph Agents │  │   PostgreSQL 16     │  │    Redis 7       │  │
│  │   (8 agents)       │  │   (Port 5432)       │  │   (Port 6379)   │  │
│  │   AI Orchestration │  │   Persistent Store  │  │   Cache/Queue   │  │
│  └───────────┬────────┘  └────────────────────┘  └──────────────────┘  │
│              │                                                           │
│  ┌───────────▼────────────────────────────────────────────────────────┐ │
│  │                      AI Provider Layer                             │ │
│  │   Groq (primary) │ Claude (secondary) │ OpenAI (tertiary)         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     Observability Stack                          │   │
│  │   Prometheus │ Grafana │ OpenTelemetry Collector                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

## Level 3: Component Diagram (Backend)

```
FastAPI Backend
├── api/
│   ├── routes/
│   │   ├── scan.py          POST /scan
│   │   ├── munit.py         POST /generate-munit
│   │   ├── execution.py     POST /execute-tests
│   │   ├── coverage.py      POST /coverage
│   │   ├── failures.py      POST /analyze-failures
│   │   ├── migration.py     POST /migration-analysis
│   │   ├── dashboard.py     GET  /dashboard
│   │   ├── reports.py       GET  /executive-report
│   │   └── auth.py          POST /auth/login
│   └── deps.py              JWT auth dependencies
│
├── agents/                  LangGraph agents (8)
│   ├── discovery_agent.py
│   ├── flow_analysis_agent.py
│   ├── munit_generation_agent.py
│   ├── coverage_agent.py
│   ├── execution_agent.py
│   ├── failure_analysis_agent.py
│   ├── migration_agent.py
│   └── executive_reporting_agent.py
│
├── services/
│   ├── groq_service.py      Primary AI (llama-3.3-70b-versatile)
│   ├── ai_provider.py       Provider abstraction (Groq/Claude/OpenAI)
│   └── munit_generator.py   MUnit XML generation engine
│
├── parsers/
│   ├── pom_parser.py        Maven pom.xml parser
│   ├── mule_xml_parser.py   Mule 4 flow parser (lxml)
│   └── raml_parser.py       RAML 1.0/0.8 parser
│
├── models/                  SQLAlchemy 2.0 ORM
│   ├── application.py
│   ├── flow.py
│   ├── test_case.py
│   ├── test_run.py
│   ├── coverage_report.py
│   ├── failure_report.py
│   ├── migration_report.py
│   └── user.py
│
└── utils/
    ├── logging.py           Structured JSON logging (structlog)
    ├── exceptions.py        Centralized exception hierarchy
    └── security.py          JWT + RBAC + password hashing
```

## API Led Connectivity Classification

```
Experience APIs (Layer 3)
    │  Consumer-facing, channel-specific
    │  Examples: mobile-exp-api, web-exp-api
    │
    ▼
Process APIs (Layer 2)
    │  Business logic, orchestration
    │  Examples: order-process-api, payment-process-api
    │
    ▼
System APIs (Layer 1)
    │  Direct system access, CRUD
    │  Examples: salesforce-sys-api, db-sys-api
    ▼
Backend Systems (DB, Salesforce, SAP, etc.)
```
