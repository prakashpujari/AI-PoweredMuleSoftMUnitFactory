# AI-MUnit-Factory

**Production-Grade Enterprise Platform for AI-Powered MuleSoft MUnit Test Generation**

[![CI/CD](https://github.com/prakashpujari/AI-PoweredMuleSoftMUnitFactory/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/prakashpujari/AI-PoweredMuleSoftMUnitFactory/actions)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.124-009688.svg)](https://fastapi.tiangolo.com)
[![Render](https://img.shields.io/badge/backend-Render-46E3B7.svg)](https://render.com)
[![Vercel](https://img.shields.io/badge/frontend-Vercel-000000.svg)](https://vercel.com)

---

## Live Infrastructure

| Service | Provider | Endpoint |
|---------|----------|----------|
| **Backend API** | Render (Oregon) | `https://ai-munit-factory.onrender.com` *(set after first deploy)* |
| **Frontend** | Vercel | `https://ai-munit-factory.vercel.app` *(set after first deploy)* |
| **PostgreSQL 18.3** | Render (Oregon) | `dpg-d84sbagjo89c73bskf10-a.oregon-postgres.render.com:5432` |
| **Redis** | Render | `red-d836e2t7vvec73938sl0:6379` |
| **Pinecone Vector DB** | Pinecone (AWS us-east-1) | `https://mortgageindex-96hwyzx.svc.aped-4627-b74a.pinecone.io` |
| **AI — Primary** | Groq | `https://api.groq.com` — `llama-3.3-70b-versatile` |
| **AI — Secondary** | Anthropic | `https://api.anthropic.com` — `claude-sonnet-4-6` |
| **AI — Tertiary** | OpenAI | `https://api.openai.com` — `gpt-4o` |

---

## API Reference

Base URL (production): `https://ai-munit-factory.onrender.com/api/v1`
Interactive docs: `https://ai-munit-factory.onrender.com/api/v1/docs`

### Authentication

```bash
# Get JWT token
POST /api/v1/auth/login
Content-Type: application/json
{"username": "admin", "password": "<password>"}

# All other endpoints require:
Authorization: Bearer <token>
```

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Platform health check |
| `POST` | `/api/v1/auth/login` | Obtain JWT access token |
| `POST` | `/api/v1/scan` | Discover & inventory a MuleSoft application |
| `POST` | `/api/v1/generate-munit` | AI-generate 18 MUnit test types per flow |
| `POST` | `/api/v1/execute-tests` | Run `mvn clean test`, collect Surefire results |
| `POST` | `/api/v1/coverage` | Analyze flow/processor/error-handler coverage |
| `POST` | `/api/v1/analyze-failures` | LLM root-cause analysis of test failures |
| `POST` | `/api/v1/migration-analysis` | Migration risk assessment (Mule 4.x → 4.9) |
| `GET` | `/api/v1/dashboard` | Real-time KPI dashboard data |
| `GET` | `/api/v1/executive-report` | Full executive scorecard |
| `GET` | `/api/v1/applications` | List all inventoried applications |
| `GET` | `/api/v1/applications/{id}` | Single application detail |

### Example Calls

```bash
BASE=https://ai-munit-factory.onrender.com
TOKEN=<your-jwt-token>

# Health
curl $BASE/health

# Scan a MuleSoft project
curl -X POST $BASE/api/v1/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/mule-project", "api_type": "process", "ai_provider": "groq"}'

# Generate MUnit tests
curl -X POST $BASE/api/v1/generate-munit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"application_id": "<app-uuid>", "ai_provider": "groq"}'

# Executive report
curl $BASE/api/v1/executive-report \
  -H "Authorization: Bearer $TOKEN"
```

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

<img width="1408" height="768" alt="AI-MUnit-Factory Architecture" src="https://github.com/user-attachments/assets/ee6efd83-829f-46a8-84ab-41a10cff3400" />

```
┌──────────────────────────────────────────────────────────────────────┐
│                         AI-MUnit-Factory                             │
│                                                                      │
│  React + TypeScript + Material UI  ──►  FastAPI (Python 3.12)       │
│                     (Vercel)                  (Render — Oregon)      │
│                                              │                       │
│              ┌───────────────────────────────┴──────────────────┐   │
│              │         LangGraph Agent Pipeline (8 Agents)       │   │
│              │  Discovery → Flow Analysis → MUnit Gen →          │   │
│              │  Coverage → Execution → Failure Analysis →        │   │
│              │  Migration → Executive Reporting                  │   │
│              └───────────────────────────────────────────────────┘   │
│                    │                    │                             │
│          AI Providers              Data Layer                        │
│    Groq (llama-3.3-70b)        PostgreSQL 18.3 (Render Oregon)      │
│    Claude Sonnet 4.6           Redis (Render)                       │
│    OpenAI GPT-4o               Pinecone mortgageindex               │
│                                                                      │
│  Observability: Prometheus + Grafana + OpenTelemetry                │
│  CI/CD: GitHub Actions (8 stages) → Render + Vercel                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Local Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/prakashpujari/AI-PoweredMuleSoftMUnitFactory.git
cd AI-PoweredMuleSoftMUnitFactory
cp .env.example .env
# Fill in credentials (see Environment Variables below)

# 2. Start full stack
docker-compose up -d

# 3. Access locally
#   API docs:   http://localhost:8000/api/v1/docs
#   Frontend:   http://localhost:3000
#   Grafana:    http://localhost:3001
#   Prometheus: http://localhost:9090
```

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async URL | `postgresql+asyncpg://user:pass@host/db?ssl=require` |
| `REDIS_URL` | Redis connection URL | `redis://host:6379` |
| `GROQ_API_KEY` | Groq API key (primary AI) | `gsk_...` |
| `ANTHROPIC_API_KEY` | Claude API key (secondary) | `sk-ant-...` |
| `OPENAI_API_KEY` | OpenAI key (tertiary) | `sk-...` |
| `PINECONE_API_KEY` | Pinecone API key | `pcsk_...` |
| `PINECONE_HOST` | Pinecone index host | `https://mortgageindex-96hwyzx.svc.aped-4627-b74a.pinecone.io` |
| `PINECONE_INDEX_NAME` | Index name | `mortgageindex` |
| `SECRET_KEY` | JWT signing key (256-bit) | `<random hex>` |
| `APP_ENV` | Runtime environment | `production` |

Copy `.env.example` to `.env` — all keys shown with their required format.

---

## CI/CD Pipeline (8 Stages)

```
push → main
  │
  ├── 1. Static Analysis     (ruff, mypy, tsc)
  ├── 2. Backend Unit Tests  (pytest 41 tests, coverage ≥ 80%)
  ├── 3. Frontend Build      (tsc + vite build)
  ├── 4. MUnit Gen Validate  (smoke-test AI generation engine)
  ├── 5. Docker Build & Push (ghcr.io images)
  ├── 6. Deploy → Render     (backend API, auto-deploy via Render API)
  ├── 7. Deploy → Vercel     (frontend SPA, vercel deploy --prod)
  └── 8. Smoke Tests         (/health + frontend reachability)
```

---

## MUnit Test Types (18 per flow)

`happy_path` · `negative_path` · `missing_payload` · `null_values` · `invalid_datatype` ·
`validation_failure` · `database_failure` · `salesforce_failure` · `kafka_failure` · `jms_failure` ·
`timeout` · `retry` · `oauth_failure` · `jwt_failure` · `client_id_failure` · `rate_limit` ·
`large_payload` · `concurrent_requests`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Material UI 6, Recharts, Vite |
| Backend | FastAPI 0.124, Python 3.12, SQLAlchemy 2.0 async |
| AI/LLM | LangGraph, Groq llama-3.3-70b, Claude Sonnet 4.6, GPT-4o |
| Database | PostgreSQL 18.3 (Render), Redis (Render), Pinecone |
| Observability | Prometheus, Grafana, OpenTelemetry |
| Deployment | Docker, Kubernetes manifests, GitHub Actions, Render, Vercel |

---

## Screenshots

| Dashboard | Applications | Executive Report |
|-----------|-------------|-----------------|
| ![Dashboard](docs/screenshots/01-dashboard.png) | ![Applications](docs/screenshots/03-applications.png) | ![Executive Report](docs/screenshots/04-executive-report.png) |

---

## Running Tests

```bash
cd backend
pytest tests/test_parsers.py tests/test_agents.py -v
# 41 passed
```

---

## License

MIT © 2025 AI-MUnit-Factory
