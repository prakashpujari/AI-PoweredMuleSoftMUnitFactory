# AI-MUnit-Factory — Live Endpoints & Infrastructure

## Deployed Services

| Service | URL | Region | Provider |
|---------|-----|--------|----------|
| **Backend API** | `https://ai-munit-factory.onrender.com` | Oregon (US West) | Render |
| **API Docs (Swagger)** | `https://ai-munit-factory.onrender.com/api/v1/docs` | — | Render |
| **API Docs (ReDoc)** | `https://ai-munit-factory.onrender.com/api/v1/redoc` | — | Render |
| **Frontend** | `https://ai-munit-factory.vercel.app` | Global CDN | Vercel |

> Note: Backend URL is confirmed after first Render deploy. Update this file with the actual service URL from the Render dashboard.

---

## Database

| Field | Value |
|-------|-------|
| Provider | Render Managed PostgreSQL |
| Version | PostgreSQL 18.3 |
| Host | `dpg-d84sbagjo89c73bskf10-a.oregon-postgres.render.com` |
| Port | `5432` |
| Database | `ai_apps_db_nzf4` |
| User | `ai_apps_db_nzf4_user` |
| SSL | `sslmode=require` (enforced) |
| Region | Oregon (US West) |
| Pool Size | 10 connections + 20 overflow |

**Async connection string (used by backend):**
```
postgresql+asyncpg://ai_apps_db_nzf4_user:<password>@dpg-d84sbagjo89c73bskf10-a.oregon-postgres.render.com/ai_apps_db_nzf4
```

---

## Redis

| Field | Value |
|-------|-------|
| Provider | Render Managed Redis |
| Host | `red-d836e2t7vvec73938sl0` |
| Port | `6379` |
| URL | `redis://red-d836e2t7vvec73938sl0:6379` |
| Usage | Session cache, agent task queue, rate limiting |

---

## Vector Database (Pinecone)

| Field | Value |
|-------|-------|
| Provider | Pinecone |
| Project | Mortgage |
| Index | `mortgageindex` |
| Host | `https://mortgageindex-96hwyzx.svc.aped-4627-b74a.pinecone.io` |
| Cluster | `aped-4627-b74a` |
| Dimension | 1536 |
| Usage | Flow embeddings, similarity search for test pattern reuse |

---

## AI Providers

| Provider | Model | Role | Endpoint |
|----------|-------|------|----------|
| **Groq** | `llama-3.3-70b-versatile` | Primary — MUnit generation, failure analysis | `https://api.groq.com/openai/v1` |
| **Anthropic** | `claude-sonnet-4-6` | Secondary — executive summaries, complex reasoning | `https://api.anthropic.com/v1` |
| **OpenAI** | `gpt-4o` | Tertiary fallback | `https://api.openai.com/v1` |

Provider selection is per-request via `ai_provider` field (`groq` / `anthropic` / `openai`).

---

## REST API — Full Reference

### Base URL
```
Production:  https://ai-munit-factory.onrender.com
Local dev:   http://localhost:8000
```

### Authentication

```http
POST /api/v1/auth/login
Content-Type: application/json

{"username": "admin", "password": "<password>"}
```

Response:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 28800
}
```

All subsequent requests:
```
Authorization: Bearer <access_token>
```

---

### Health

```http
GET /health
```

```json
{"status": "healthy", "version": "1.0.0", "environment": "production"}
```

---

### Applications

```http
GET /api/v1/applications?limit=200&offset=0
```
List all scanned applications.

```http
GET /api/v1/applications/{application_id}
```
Single application with flows, scores, and test run history.

---

### Scan

```http
POST /api/v1/scan
Content-Type: application/json
Authorization: Bearer <token>

{
  "repo_path": "/path/to/mule-project",
  "business_unit": "Commerce",
  "domain": "order-management",
  "environment": "production",
  "api_type": "process",          // system | process | experience | unknown
  "ai_provider": "groq"           // groq | anthropic | openai
}
```

Response: `{"application_id": "<uuid>", "status": "discovered", "flows_count": 12}`

---

### MUnit Generation

```http
POST /api/v1/generate-munit
Content-Type: application/json
Authorization: Bearer <token>

{
  "application_id": "<uuid>",
  "ai_provider": "groq",
  "test_types": ["happy_path", "negative_path", "timeout"]   // optional — defaults to all 18
}
```

Response: `{"test_cases_generated": 216, "munit_files": {"order-flow-test.xml": "..."}}`

---

### Execute Tests

```http
POST /api/v1/execute-tests
Content-Type: application/json
Authorization: Bearer <token>

{"application_id": "<uuid>"}
```

Response: `{"test_run_id": "<uuid>", "status": "running"}`

---

### Coverage

```http
POST /api/v1/coverage
Content-Type: application/json
Authorization: Bearer <token>

{"application_id": "<uuid>", "test_run_id": "<uuid>"}
```

```json
{
  "flow_coverage": 97.2,
  "processor_coverage": 94.8,
  "error_handler_coverage": 91.5,
  "overall_coverage": 94.5,
  "meets_target": true
}
```

---

### Failure Analysis

```http
POST /api/v1/analyze-failures
Content-Type: application/json
Authorization: Bearer <token>

{"application_id": "<uuid>", "test_run_id": "<uuid>"}
```

Returns LLM root-cause analysis per failure, categorized by type (configuration, logic, dependency, data).

---

### Migration Analysis

```http
POST /api/v1/migration-analysis
Content-Type: application/json
Authorization: Bearer <token>

{
  "application_id": "<uuid>",
  "source_version": "4.4.0",
  "target_version": "4.9.0"
}
```

Returns risk score, breaking changes, recommended actions.

---

### Dashboard

```http
GET /api/v1/dashboard
Authorization: Bearer <token>
```

```json
{
  "total_applications": 127,
  "total_tests": 15420,
  "pass_rate": 98.4,
  "avg_coverage": 95.7,
  "failure_by_severity": {...},
  "recent_test_runs": [...]
}
```

---

### Executive Report

```http
GET /api/v1/executive-report
Authorization: Bearer <token>
```

```json
{
  "applications_scanned": 127,
  "applications_tested": 112,
  "tests_executed": 15420,
  "pass_rate": 98.4,
  "coverage_percent": 95.7,
  "risk_level": "LOW",
  "production_readiness": 96.2,
  "recommendation": "APPROVED FOR PRODUCTION",
  "business_unit_breakdown": [...],
  "api_type_breakdown": [...]
}
```

---

## GitHub Actions Secrets Required

| Secret | Description |
|--------|-------------|
| `GROQ_API_KEY` | Groq API key for MUnit generation |
| `PINECONE_API_KEY` | Pinecone key for vector search |
| `RENDER_API_KEY` | Render deploy API key |
| `RENDER_SERVICE_ID` | Render web service ID (`srv-xxxxx`) |
| `RENDER_BACKEND_URL` | Live Render URL for smoke tests |
| `VERCEL_TOKEN` | Vercel deploy token |
| `VERCEL_FRONTEND_URL` | Live Vercel URL for smoke tests |
| `ANTHROPIC_API_KEY` | Claude API key (optional — fallback) |
| `OPENAI_API_KEY` | OpenAI key (optional — fallback) |
