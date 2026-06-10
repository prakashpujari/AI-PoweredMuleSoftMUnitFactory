# AI-MUnit-Factory

**Production-Grade Enterprise Platform for AI-Powered MuleSoft MUnit Test Generation**

[![CI/CD](https://github.com/mailtopprakash05/AI-PoweredMuleSoftMUnitFactory/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/mailtopprakash05/AI-PoweredMuleSoftMUnitFactory/actions)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)

---

## Overview

AI-MUnit-Factory automatically:
1. **Discovers** MuleSoft apps (pom.xml, Mule XML, RAML)
2. **Analyzes** flows, connectors, DataWeave
3. **Generates** MUnit 2.x suites via AI (Groq llama-3.3-70b / Claude / OpenAI)
4. **Executes** `mvn clean test` and collects Surefire/MUnit reports
5. **Analyzes** failures with LLM root cause analysis
6. **Measures** flow, processor, error-handler coverage (target: 95%+)
7. **Assesses** migration risk (Mule 4.4/4.6 → 4.9)
8. **Reports** via executive dashboards and PDF scorecards

---

## Architecture

<img width="1408" height="768" alt="Gemini_Generated_Image_kzrmimkzrmimkzrm" src="https://github.com/user-attachments/assets/ee6efd83-829f-46a8-84ab-41a10cff3400" />

```
┌──────────────────────────────────────────────────────────────────────┐
│                         AI-MUnit-Factory                             │
│                                                                      │
│  React + TypeScript + Material UI  ──►  FastAPI (Python 3.12)       │
│                                              │                       │
│              ┌───────────────────────────────┴──────────────────┐   │
│              │         LangGraph Agent Pipeline (8 Agents)       │   │
│              │  Discovery → Flow Analysis → MUnit Gen →          │   │
│              │  Coverage → Execution → Failure Analysis →        │   │
│              │  Migration → Executive Reporting                  │   │
│              └───────────────────────────────────────────────────┘   │
│                    │                    │                             │
│          AI Providers              Data Layer                        │
│    Groq (llama-3.3-70b)        PostgreSQL + Redis                   │
│    Claude Sonnet 4.6           Pinecone (vectors)                   │
│    OpenAI GPT-4o                                                    │
│                                                                      │
│  Observability: Prometheus + Grafana + OpenTelemetry                │
│  Deployment: Docker + Kubernetes + GitHub Actions CI/CD             │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Configure
cp .env.example .env
# Add GROQ_API_KEY to .env

# 2. Start platform
docker-compose up -d

# 3. Access
#   API:        http://localhost:8000/api/v1/docs
#   Frontend:   http://localhost:3000
#   Grafana:    http://localhost:3001
#   Prometheus: http://localhost:9090

# 4. Scan first app
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"repo_path": "/path/to/mule-project", "api_type": "process"}'

# 5. Generate tests
curl -X POST http://localhost:8000/api/v1/generate-munit \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"application_id": "<id>"}'
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/scan` | Discover & inventory application |
| `POST /api/v1/generate-munit` | AI-generate MUnit tests |
| `POST /api/v1/execute-tests` | Run `mvn clean test` |
| `POST /api/v1/coverage` | Analyze coverage |
| `POST /api/v1/analyze-failures` | LLM failure root cause |
| `POST /api/v1/migration-analysis` | Migration risk assessment |
| `GET /api/v1/dashboard` | Real-time KPI dashboard |
| `GET /api/v1/executive-report` | Full executive report |

---

## Executive Report Output

```
Applications Scanned:        120
Tests Executed:           15,000
Passed:                   14,750
Failed:                      250
Pass Rate:                 98.3%
Coverage:                  95.0%
Security Score:               97
Performance Score:            95
Production Readiness:      96/100
Risk Level:                  LOW
Recommendation: APPROVED FOR PRODUCTION
```

---

## MUnit Test Types (18 per flow)

happy_path · negative_path · missing_payload · null_values · invalid_datatype ·
validation_failure · database_failure · salesforce_failure · kafka_failure · jms_failure ·
timeout · retry · oauth_failure · jwt_failure · client_id_failure · rate_limit ·
large_payload · concurrent_requests

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, TypeScript, Material UI 6, Recharts |
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.0 async |
| AI/LLM | LangGraph, Groq (llama-3.3-70b), Claude Sonnet, GPT-4o |
| Database | PostgreSQL 16, Redis 7, Pinecone |
| Observability | Prometheus, Grafana, OpenTelemetry |
| Deployment | Docker, Kubernetes, GitHub Actions |

---

## Running Tests

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## License

MIT © 2025 AI-MUnit-Factory
