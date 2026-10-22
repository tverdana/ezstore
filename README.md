# EZStore

> A lightweight B2B quotation and order management system.

[中文版](README.zh-TW.md)

---

## Part 1 — For Developers

### Overview

EZStore provides four core modules for managing the B2B sales pipeline:

| Module | Description |
|--------|-------------|
| **Customer Management** | CRUD for companies — name, tax ID, contacts, address, customer level (VIP / Standard / New), credit score |
| **Product Management** | CRUD for products — product number, name, description, cost, list price, inventory, supplier |
| **Quotation Management** | Create, edit, publish, and delete quotations. Pricing is computed from a *pricing factor* applied to list prices. Published quotations become immutable. |
| **Order Management** | CRUD for orders — optionally linked to a published quotation |
| **AI Agent** | Natural language quotation assistant — query, duplicate, adjust pricing factor/total price, convert to order. Google ADK 2.x graph Workflow + Gemini 3.8 Flash + MCP Server, scaffolded with google-agents-cli. |

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Go 1.25 · Gin · GORM · Swagger (swaggo) · Testify |
| Frontend | React 19 · TypeScript · Tailwind CSS 4 · Vite 8 · TanStack React Query · React Hook Form · React Router |
| Database | PostgreSQL 16 |
| AI Agent | Python 3.12 · Google ADK 2.10+ (graph Workflow API) · google-agents-cli 1.11 · Gemini 3.8 Flash · MCP Python SDK 2.x (Streamable HTTP) · uv |
| Build & Deploy | Docker · Docker Compose · Bun (frontend) · Nginx (frontend serving & API proxy) |

### Project Structure

```
ezstore/
├── docker-compose.yml          # Orchestrates all services
├── scripts/
│   └── seed-test-data.sql      # Idempotent test dataset (TRUNCATE + INSERT)
├── .env.example                # GEMINI_API_KEY and agent settings (copy to .env)
├── agent/                      # ADK 2.x graph Workflow agent, built from agent-spec-prompt.md (see agent/README.md)
│   ├── Dockerfile
│   ├── pyproject.toml           # google-adk[mcp,a2a]>=2.10,<3 (+ uv.lock)
│   ├── quotation_agent/         # agent.py (Workflow), fast_api_app.py (ADK FastAPI + A2A)
│   └── tests/                   # unit/, integration/, eval/ (datasets + eval_config.yaml)
├── mcp_server/
│   ├── Dockerfile
│   ├── pyproject.toml           # mcp>=2.2, httpx (+ uv.lock)
│   └── server.py                # MCPServer (Streamable HTTP) with 6 quotation tools
├── backend/
│   ├── Dockerfile
│   ├── main.go                 # Entry point — Gin + GORM + Swagger init
│   ├── config/config.go        # Database connection (env vars)
│   ├── models/                 # GORM models (Customer, Product, Quotation, Order + items)
│   ├── repositories/           # Data access layer (CRUD, pagination, search)
│   ├── services/               # Business logic (pricing engine, validation)
│   ├── handlers/               # Gin HTTP handlers + Swagger annotations
│   ├── middleware/              # CORS, error handling
│   ├── routes/routes.go        # Route registration
│   └── docs/                   # Auto-generated Swagger files
└── frontend/
    ├── Dockerfile
    ├── nginx.conf              # Reverse proxy /api → backend, SPA fallback
    ├── vite.config.ts
    ├── src/
    │   ├── api/                # Axios API clients
    │   ├── pages/              # Route-level page components
    │   ├── components/         # Shared UI (DataTable, Pagination, StatusBadge, etc.)
    │   ├── types/index.ts      # TypeScript type definitions
    │   ├── App.tsx             # Router + QueryClientProvider
    │   └── main.tsx            # React entry point
    └── e2e/                    # Playwright E2E tests (planned)
```

### Prerequisites

The following tools must be installed before developing or running EZStore:

| Tool | Version | Purpose |
|------|---------|---------|
| **Docker** | ≥ 24.0 | Container runtime for all services |
| **Docker Compose** | ≥ 2.20 (included with Docker Desktop) | Multi-container orchestration |
| **Go** | ≥ 1.24 | Backend compilation and development |
| **Bun** | ≥ 1.0 | Frontend package manager and build tool |
| **swag** (Go CLI) | latest | Swagger documentation generation |

> **Docker-only mode:** If you only need to *run* EZStore (not develop), Docker and Docker Compose are sufficient. Go, Bun, and swag are only needed for local development.

#### macOS

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Docker Desktop (includes Docker Compose)
brew install --cask docker

# Go
brew install go

# Bun
brew install oven-sh/bun/bun

# swag (Swagger CLI) — requires Go to be installed first
go install github.com/swaggo/swag/cmd/swag@latest
```

After installing Docker Desktop, launch it from Applications and ensure it is running (whale icon in the menu bar).

#### Windows

```powershell
# Install winget (comes with Windows 11; for Windows 10 install "App Installer" from Microsoft Store)

# Docker Desktop (includes Docker Compose)
winget install Docker.DockerDesktop

# Go
winget install GoLang.Go

# Bun
powershell -c "irm bun.sh/install.ps1 | iex"

# swag (Swagger CLI) — requires Go to be installed first; restart terminal after Go install
go install github.com/swaggo/swag/cmd/swag@latest
```

After installing Docker Desktop, launch it and ensure **WSL 2 backend** is enabled (Settings → General → Use the WSL 2 based engine). You may need to restart your computer.

> **Note for Windows users:** All shell commands in this README use Unix-style syntax. Use **Git Bash**, **WSL 2**, or **PowerShell** to run them. If using PowerShell, replace `export VAR=value` with `$env:VAR="value"`.

#### Verify Installation

```bash
docker --version          # Docker version 24.x+
docker compose version    # Docker Compose version v2.x+
go version                # go1.24+
bun --version             # 1.x+
swag --version            # swag version v1.x+
```

### Quick Start (Docker Compose)

**API key (required for the AI Agent, everything else runs without it):**

```bash
cp .env.example .env      # then fill in GEMINI_API_KEY from https://aistudio.google.com/apikey
```

**Option A — Use pre-built images from GHCR (default, no build required):**

```bash
docker compose up -d
```

**Option B — Build from local source code:**

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build
```

**Load test data:**

```bash
docker compose exec db psql -U ezstore -f /scripts/seed-test-data.sql
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8080/api/v1 |
| Swagger UI | http://localhost:8080/swagger/index.html |
| Health Check | http://localhost:8080/health |

**Run E2E tests (verify the deployment is working):**

```bash
docker compose exec db psql -U ezstore -f /scripts/seed-test-data.sql
docker compose run --rm e2e
```

### Development Mode

```bash
# 1. Start PostgreSQL
docker compose up db -d

# 2. Start backend (hot reload with go run)
cd backend
export DB_HOST=localhost DB_PORT=5432 DB_USER=ezstore DB_PASSWORD=ezstore DB_NAME=ezstore
go run .

# 3. Start frontend (Vite dev server with API proxy)
cd frontend
bun install
bun run dev          # http://localhost:5173
```

### API Documentation

All endpoints are documented with Swagger annotations. Once the backend is running, visit:

```
http://localhost:8080/swagger/index.html
```

### Testing

**Backend unit tests:**

```bash
cd backend
go test ./... -v -cover
```

**Load test dataset** (idempotent — safe to run repeatedly):

```bash
docker compose exec db psql -U ezstore -f /scripts/seed-test-data.sql
```

The seed data includes: 15 customers (5 VIP + 6 Standard + 4 New), 20 products, 12 quotations (8 published + 4 draft), 10 orders (3 pending + 3 confirmed + 2 completed + 2 cancelled).

**Regenerate Swagger docs:**

```bash
cd backend
$(go env GOPATH)/bin/swag init -g main.go --parseDependency --parseInternal
```

### Core Business Logic

**Pricing Factor** — Determines how list prices are adjusted per customer level:

| Customer Level | Default Factor | Effect |
|---------------|----------------|--------|
| VIP | 0.80 | 20% discount |
| Standard | 0.90 | 10% discount |
| New | 1.00 | Full price |

The factor can be manually adjusted per quotation.

**Computation Formulas:**

```
unit_price   = list_price × pricing_factor
subtotal     = unit_price × quantity
total_price  = Σ(subtotal)
profit       = Σ((unit_price − cost) × quantity)
profit_rate  = profit ÷ total_price
```

**Publish Immutability** — Once a quotation is published:
- It cannot be edited (HTTP 403)
- It cannot be deleted (HTTP 403)
- It cannot be published again (HTTP 400)

### AI Agent

> `agent/` was built on this branch from `agent-spec-prompt.md` (stages 4.1–4.5, one commit per stage). Design notes and how to add an operation: [agent/README.md](agent/README.md).

EZStore includes a natural-language quotation assistant built with Google ADK 2.x (`google-adk[mcp,a2a]>=2.10,<3`, Python 3.12). The agent is a **graph Workflow**: only one node calls the LLM (intent classification); tool selection, tool arguments, clarification and refusal are all decided by code.

**Architecture:**

```
User → React Chat UI → nginx /agent-api → Agent (ADK FastAPI, port 8080, internal) → MCP Server (port 8000) → Backend REST API
                                               │                                         Streamable HTTP
                                          Gemini 3.8 Flash                               (mcp Python SDK 2.x)
                                  (AI Studio API key or Vertex AI)
```

**Workflow graph** (`agent/quotation_agent/agent.py`, ADK app name `quotation_agent`):

```
START → prepare_input → classify_intent (LLM, output_schema=IntentResult) → route_intent
          ├─ get_quotation / list_customer_quotations / duplicate_quotation
          ├─ update_pricing_factor / adjust_total_price / convert_to_order    ← each calls exactly one MCP tool
          ├─ clarify   (a required field is missing → ask for it; operation kept in state.pending_operation)
          └─ refuse    (fixed refusal text, decided by code)
        all → respond  (the only node whose text the Chat UI shows)
```

| Node | Type | What it does |
|------|------|--------------|
| `prepare_input` | function | Builds the classifier input: last 6 messages of session history, the pending operation (if any) and the current message |
| `classify_intent` | `LlmAgent` | The only LLM call. Returns `IntentResult` (intent + quotation number / customer name / pricing factor / target total), temperature 0, no conversation contents of its own |
| `route_intent` | function | Picks the next node with `Event(route=...)`: refuses off-topic intents and customer/product CRUD requests (regex guard), validates the `QT-YYYYMMDD-NNN` format, merges a pending operation, asks for missing fields |
| 6 operation nodes | function | Call one MCP tool each through `McpToolset` + `StreamableHTTPConnectionParams(MCP_URL)` and return the tool text unchanged; tool errors become `操作失敗：…` |
| `clarify` / `refuse` | function | Pass the question / refusal text built by `route_intent` |
| `respond` | function | Emits the final text; the frontend only displays events whose `nodeInfo.path` ends in `/respond@<n>` |

Every user message re-runs the graph from `START`. A follow-up answer works in two ways: `route_intent` stores the waiting operation in session state, and `prepare_input` passes recent history to the classifier, so the follow-up also works when earlier turns are only seeded as events (which is what `agents-cli eval` does for multi-turn cases).

**Capabilities:**

| Operation | Description |
|-----------|-------------|
| Query quotation | Look up quotation details by quotation number (uses `GET /quotations?quotation_number=`) |
| List customer quotations | List all quotations for a given customer name |
| Duplicate quotation | Create a new draft copy of a quotation |
| Modify pricing factor | Duplicate first, then update the pricing factor on the copy |
| Modify total price | Duplicate first, then binary-search the pricing factor (≤ 20 iterations) to reach a target total |
| Convert to order | Create an order from the quotation's customer and items, linked via `quotation_id`; the quotation itself is untouched |

**Key design:**
- All modifications use **copy-on-write**. The original quotation is never changed, and the reply says so (the MCP tool text, shown verbatim, contains `（未修改）`)
- All responses include **plain-text system links** (`http://localhost:3000/quotations/<id>`, `/orders/<id>`), never Markdown links
- Off-topic requests are **refused by code**; missing fields trigger a **clarification turn** that the next message completes
- Model calls retry **429 and 503 with exponential backoff** (google-genai `HttpRetryOptions`: 4 attempts, about 2 s / 4 s / 8 s plus jitter). If the quota is still exhausted, the user gets a clear `RESOURCE_EXHAUSTED` message instead of a stack trace
- The agent starts without any credentials (chat returns a clear "credentials not set" error), so `docker compose up` never fails on a missing key

**Environment variables:**

| Variable | Set in | Purpose |
|----------|--------|---------|
| `GEMINI_API_KEY` | root `.env` (Compose) · `agent/.env` (local) | Google AI Studio key for the classifier (and the eval quality judge) |
| `GOOGLE_GENAI_USE_VERTEXAI` | root `.env` · `agent/.env` | `FALSE` = AI Studio (default); `true` = run the agent's model on Vertex AI |
| `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` | root `.env` · `agent/.env` | Vertex AI project / location (`global`). Needed locally for `agents-cli eval` grading even with AI Studio, see below |
| `AGENT_MODEL` | root `.env` · `agent/.env` | Model name, default `gemini-3.8-flash` (also used by the quality judge) |
| `MCP_URL` | Compose: `http://mcp-server:8000/mcp` · `agent/.env`: `http://localhost:8010/mcp` | MCP Server endpoint |
| `FRONTEND_URL` | root `.env` (mcp-server) · `agent/.env` | Base URL of the system links (they are generated by the MCP Server) |
| `ALLOW_ORIGINS` | root `.env` | CORS origins of the agent API |
| `MCP_HOST_PORT` | root `.env` | Host port of the MCP Server, default `8010` |

In Compose the agent listens on port 8080 **inside the Docker network only** (host port 8080 is the backend). The Chat UI reaches it through nginx at `/agent-api/`. Vertex AI inside Docker also needs the ADC file mounted; see the commented lines of the `agent` service in `docker-compose.yml`.

**Local development** (db, backend and mcp-server running in Compose; mcp-server is exposed on host port 8010):

```bash
cd agent
cp .env.example .env                 # set GEMINI_API_KEY; keep GOOGLE_GENAI_USE_VERTEXAI=FALSE and MCP_URL=http://localhost:8010/mcp
uv sync --group dev --extra eval
agents-cli playground --port 8501    # use 8501: port 8080 is taken by the backend
                                     # open http://127.0.0.1:8501/dev-ui/?app=quotation_agent
agents-cli run "我要查詢報價單，報價單編號：QT-20260330-001"
```

**Tests:**

```bash
uv run pytest tests/unit -q                              # no LLM, no MCP: routing rules + model retry/429 against a local fake Gemini endpoint
uv run --env-file .env pytest tests/integration -q       # real model (3 calls): runner, /run_sse, A2A stream, agent card (uses port 8000)
agents-cli eval run                                      # read-only smoke set (tests/eval/datasets/basic-dataset.json)
agents-cli eval run --dataset tests/eval/datasets/quotation-guardrails.json --config tests/eval/eval_config.yaml   # 2 refusals + 1 multi-turn
docker compose exec db psql -U ezstore -f /scripts/seed-test-data.sql   # (repo root) reseed before the actions set
agents-cli eval run --dataset tests/eval/datasets/quotation-actions.json --config tests/eval/eval_config.yaml      # 6 operations, creates data
python3 scripts/grading/grade_agent.py --suite scripts/grading/student-suite.json --runs 2                          # (repo root) self-acceptance score 0–100
```

> **Eval grading needs Google Cloud, even with an AI Studio key.** With agents-cli 1.11 and google-cloud-aiplatform 2.6.0, `agents-cli eval grade` fails without Application Default Credentials. The eval SDK always constructs a Cloud Storage client, even when only code metrics run. `prompt_template` judges such as `refusal_or_action` also run on the **Vertex AI Eval Service**, which needs a project. One-time setup:
> 1. `gcloud auth application-default login`
> 2. Pick a project with billing, enable the Vertex AI API (`aiplatform.googleapis.com`), and add `GOOGLE_CLOUD_PROJECT=<project-id>` and `GOOGLE_CLOUD_LOCATION=global` to `agent/.env`. Keep `GEMINI_API_KEY` and `GOOGLE_GENAI_USE_VERTEXAI=FALSE`: the agent and the quality judge stay on AI Studio, and only the `prompt_template` judge runs on Vertex AI.
> 3. On a new project, if the judge returns `404 … Gaia id not found for email service-…@gcp-sa-aiplatform.iam.gserviceaccount.com`, create the Vertex AI service identity: `gcloud beta services identity create --service=aiplatform.googleapis.com --project=<project-id>`.

#### Evaluation report

**What was evaluated:** 11 cases. The six operations (`quotation-actions.json`), two off-topic requests and one multi-turn clarification (`quotation-guardrails.json`), plus the grader's two extra cases (a quotation that does not exist, and a request for Markdown links).

**How it was evaluated** (`agent/tests/eval/eval_config.yaml`):

| Metric | Kind | What it guards |
|--------|------|----------------|
| `custom_response_quality` | LLM judge, 1–5, local (`response_quality.py`, google-genai) | Overall accuracy and clarity against each case's `reference` |
| `link_present` | Code check, 0/1 (`link_presence.py`) | A plain-text `/quotations/<id>` or `/orders/<id>` link; Markdown links score 0; `off_topic*` cases need no link |
| `refusal_or_action` | LLM judge, 0/1, `prompt_template` on the Vertex AI Eval Service | Off-topic → refuse without tools; operation → completed with plain-text links; missing data → asking counts |
| `agent_turn_count` | Code, count | Number of turns (2 for the multi-turn case) |

The backend checks in `scripts/grading/grade_agent.py` confirm in the database that the original quotation is unchanged and that the copies and the linked order exist.

**Results:**

| Run | custom_response_quality | link_present | refusal_or_action | agent_turn_count |
|-----|-------------------------|--------------|-------------------|------------------|
| guardrails (3 cases) | 5.0 | 1.0 | 1.0 | 1.33 (multi-turn case: 2) |
| actions (6 cases, after reseed) | 5.0 | 1.0 | 1.0 | 1.0 |

Self-acceptance grading (`student-suite.json`, `--runs 2`): **99.6 / 100**. guardrails 30.0/30, actions 49.6/50 (all four backend checks passed: original untouched, 6 copies, a copy with factor 1.5, order linked to the original), extra 20.0/20. The lowest case was `get_quotation` at 90%: in one of the two runs the Vertex AI judge returned malformed JSON (`400 INVALID_ARGUMENT … Error parsing JSON`), which the grader counts as 0. The agent's reply was identical and correct in both runs.

**Stability:** across the two grading runs every case scored the same except that one judge error. The classifier runs at temperature 0, and every user-visible reply is either fixed text or verbatim MCP tool output, so replies are reproducible. Only the model's intent and parameter extraction can vary.

**Problems found and handled:**

| Problem | Handling |
|---------|----------|
| `agents-cli eval` seeds earlier turns of a multi-turn case as events and never runs them, so no session state exists for the follow-up | `prepare_input` also feeds recent session history to the classifier; `clarify_then_complete` passes |
| The multi-turn case reported `agent_turn_count` = 1 | Previous round moved to `agent_data.turns[0]`, follow-up to `turns[1]` |
| A model error or missing credentials crashed the workflow (`route_intent` received `None`) | `route_intent` now ends the turn without calling tools; the error event carries a clear message (unit-tested against a fake Gemini endpoint) |
| The free tier quota (20 requests/day) ran out during development (`429 RESOURCE_EXHAUSTED`) | Exponential-backoff retry for 429/503 and a clear quota message |
| MCP errors were shown as `Error executing tool get_quotation: …` | Prefix stripped: `操作失敗：找不到報價單編號 …` |
| Grading failed with an AI Studio key only (`DefaultCredentialsError`, then `Could not determine GCP project`, then `404 Gaia id not found` on a new project) | Google Cloud setup above (ADC, project with the Vertex AI API, service identity); the agent itself stays on AI Studio |
| `Could not fetch /app-info … grading will degrade` during generate | Expected: ADK's experimental endpoint only supports an `LlmAgent` root (`"Root agent is not an LlmAgent"`); our metrics do not use that data |

**Risks not yet covered** (next test cases): similar customer names (without an exact match the MCP Server falls back to the first fuzzy match), Chinese numerals such as 「十萬」 or 「打九折」, two operations in one message, and the deliberate "break test" from eval-lab section 7 (switch `respond` to Markdown links and confirm that `link_present` and `refusal_or_action` drop to 0).

Trustworthiness evaluation labs for learners: [eval-lab-quick.md](eval-lab-quick.md) (25 min, in class) and [eval-lab.md](eval-lab.md) (60–90 min, full version).

### License

This project is licensed under the [MIT License](LICENSE).

---

## Part 2 — For AI Coding Agents

> This section is written for AI coding assistants (Claude Code, Gemini CLI, GitHub Copilot, Antigravity, Cursor, Aider, etc.). It provides structured, machine-friendly context to help you work effectively in this codebase.

### Project Identity

- **Name:** EZStore
- **Purpose:** B2B quotation and order management system
- **Language:** Go (backend), TypeScript/React (frontend), Python 3.12 (agent + MCP server)
- **Database:** PostgreSQL 16
- **Deployment:** Docker Compose (5 services: db, backend, frontend, agent, mcp-server)

### Architecture Pattern

The backend follows a **3-layer architecture**:

```
HTTP Request → Handler (Gin) → Service (business logic) → Repository (GORM/DB)
```

- **Handlers** parse HTTP input, call services, return JSON. Include Swagger annotations.
- **Services** contain validation and business logic. Never access `*gin.Context`.
- **Repositories** wrap GORM queries. Return models or errors, never HTTP concepts.

### Key File Paths

| Concern | Path |
|---------|------|
| Backend entry point | `backend/main.go` |
| Database config | `backend/config/config.go` |
| All models | `backend/models/*.go` |
| All repositories | `backend/repositories/*.go` |
| All services | `backend/services/*.go` |
| All handlers | `backend/handlers/*.go` |
| Route registration | `backend/routes/routes.go` |
| CORS middleware | `backend/middleware/cors.go` |
| Error response helper | `backend/middleware/error_handler.go` |
| Pricing factor defaults | `backend/models/customer.go` → `DefaultPricingFactor()` |
| Quotation calculation | `backend/services/quotation_service.go` → `computeTotals()`, `buildItems()` |
| Frontend entry | `frontend/src/main.tsx` |
| React router | `frontend/src/App.tsx` |
| TypeScript types | `frontend/src/types/index.ts` |
| API clients | `frontend/src/api/*.ts` |
| Page components | `frontend/src/pages/*.tsx` |
| Shared components | `frontend/src/components/shared/*.tsx` |
| Agent workflow graph | `agent/quotation_agent/agent.py` (`Workflow`, `Intent`, `IntentResult`, node functions) |
| Agent prompts / fixed replies | `agent/quotation_agent/agent.py` (`classify_intent.instruction`, `REFUSAL_TEXT`, `ARG_LABELS`, …) |
| Agent FastAPI app | `agent/quotation_agent/fast_api_app.py` |
| Agent eval | `agent/tests/eval/eval_config.yaml`, `agent/tests/eval/link_presence.py`, `agent/tests/eval/datasets/*.json` |
| Agent unit tests | `agent/tests/unit/test_route_intent.py`, `agent/tests/unit/test_model_errors.py` |
| MCP Server (6 tools, mcp 2.x `MCPServer`) | `mcp_server/server.py` |
| Agent Chat UI | `frontend/src/pages/AgentChatPage.tsx` |
| Agent API client | `frontend/src/api/agentApi.ts` |
| Docker orchestration | `docker-compose.yml` |
| Test dataset | `scripts/seed-test-data.sql` |

### Database Schema Summary

6 tables. All main entities use GORM soft-delete (`deleted_at`). Item tables use hard delete.

```
customers         → id, name, tax_id (unique, 8 digits), contact_name, contact_phone,
                    contact_email, address, level (vip|standard|new), credit_score (0-100)

products          → id, product_number (unique), name, description, cost, list_price,
                    inventory, supplier

quotations        → id, quotation_number (unique, auto: QT-YYYYMMDD-NNN),
                    customer_id (FK), customer_level (snapshot), pricing_factor,
                    total_price, profit_amount, profit_rate,
                    status (draft|published), notes

quotation_items   → id, quotation_id (FK, CASCADE), product_id (FK),
                    product_name (snapshot), product_cost (snapshot), list_price (snapshot),
                    unit_price, quantity, subtotal

orders            → id, order_number (unique, auto: ORD-YYYYMMDD-NNN),
                    customer_id (FK), quotation_id (FK, nullable),
                    total_price, status (pending|confirmed|completed|cancelled), notes

order_items       → id, order_id (FK, CASCADE), product_id (FK),
                    product_name (snapshot), unit_price, quantity, subtotal
```

**Important:** Quotation/order items store *snapshots* of product data (name, cost, list_price) at creation time. This ensures historical accuracy if product data changes later.

### REST API Endpoints

Base path: `/api/v1`

```
GET    /health                        → { status: "ok" }
GET    /api/v1/pricing-factor/:level  → { level, pricing_factor }

# Customers
GET    /api/v1/customers              → paginated list (?page, ?page_size, ?search)
GET    /api/v1/customers/:id
POST   /api/v1/customers
PUT    /api/v1/customers/:id
DELETE /api/v1/customers/:id          → soft delete

# Products
GET    /api/v1/products               → paginated list (?page, ?page_size, ?search)
GET    /api/v1/products/:id
POST   /api/v1/products
PUT    /api/v1/products/:id
DELETE /api/v1/products/:id           → soft delete

# Quotations
GET    /api/v1/quotations             → paginated list (?page, ?page_size, ?status, ?customer_id, ?quotation_number)
GET    /api/v1/quotations/:id         → includes items[] and customer
POST   /api/v1/quotations             → body: { customer_id, pricing_factor, notes, items: [{product_id, quantity}] }
PUT    /api/v1/quotations/:id         → draft only; same body as POST
POST   /api/v1/quotations/:id/publish → sets status to published (irreversible)
DELETE /api/v1/quotations/:id         → draft only; soft delete

# Orders
GET    /api/v1/orders                 → paginated list (?page, ?page_size, ?status, ?customer_id)
GET    /api/v1/orders/:id             → includes items[] and customer
POST   /api/v1/orders                 → body: { customer_id, quotation_id?, notes, items: [{product_id, unit_price, quantity}] }
PUT    /api/v1/orders/:id
DELETE /api/v1/orders/:id             → soft delete
```

### Pricing Computation Rules

When a quotation is created or updated, the backend:

1. Fetches the customer → snapshots `customer_level`
2. For each item: fetches the product → snapshots `product_name`, `product_cost`, `list_price`
3. Computes `unit_price = list_price × pricing_factor`
4. Computes `subtotal = unit_price × quantity`
5. Computes `total_price = Σ(subtotal)`
6. Computes `profit_amount = Σ((unit_price − cost) × quantity)`
7. Computes `profit_rate = profit_amount ÷ total_price` (guarded: returns 0 if total is 0)

Default pricing factors: VIP → 0.80, Standard → 0.90, New → 1.00 (defined in `backend/models/customer.go`).

### Business Rules and Constraints

- **Tax ID**: must be exactly 8 digits (`^\d{8}$`)
- **Customer level**: must be one of `vip`, `standard`, `new`
- **Credit score**: integer 0–100
- **Product cost and list_price**: must be ≥ 0 (Decimal, never float)
- **Quantity**: must be > 0
- **Published quotation**: cannot be edited, deleted, or re-published
- **Quotation/Order numbers**: auto-generated as `QT-YYYYMMDD-NNN` / `ORD-YYYYMMDD-NNN`
- **Soft delete**: customers, products, quotations, orders use `deleted_at`
- **Hard delete**: quotation_items and order_items are physically deleted on parent update

### Common Developer Commands

```bash
# Full stack (Docker)
docker compose up --build -d
docker compose down -v                    # stop and remove volumes
docker compose exec db psql -U ezstore -f /scripts/seed-test-data.sql

# Backend
cd backend
go run .                                  # start API server (port 8080)
go test ./... -v -cover                   # run all tests
go build -o ezstore-api .                 # build binary
$(go env GOPATH)/bin/swag init -g main.go --parseDependency --parseInternal  # regenerate swagger

# Frontend
cd frontend
bun install                               # install dependencies
bun run dev                               # dev server (port 5173, proxies /api to :8080)
bun run build                             # production build → dist/

# MCP Server
cd mcp_server
uv sync && BACKEND_URL=http://localhost:8080 MCP_PORT=8010 uv run python server.py

# Agent (reads agent/.env: GEMINI_API_KEY, GOOGLE_GENAI_USE_VERTEXAI=FALSE, MCP_URL, AGENT_MODEL;
#        eval grading also needs ADC + GOOGLE_CLOUD_PROJECT, see the AI Agent section)
cd agent
uv sync --group dev --extra eval
agents-cli playground --port 8501         # local web UI (8080 is the backend)
agents-cli run "我要查詢報價單，報價單編號：QT-20260330-001"
uv run pytest tests/unit -q               # no LLM, no MCP
uv run --env-file .env pytest tests/integration -q   # real model calls
agents-cli eval run --dataset tests/eval/datasets/quotation-guardrails.json --config tests/eval/eval_config.yaml
```

### Common Modification Scenarios

**Adding a new field to an existing entity (e.g., adding `fax` to Customer):**
1. Add the field to the model in `backend/models/customer.go` (with GORM + JSON tags)
2. GORM AutoMigrate in `main.go` handles the schema change automatically
3. Update validation in `backend/services/customer_service.go` if needed
4. Update the handler's Swagger annotations in `backend/handlers/customer_handler.go`
5. Add the field to `frontend/src/types/index.ts`
6. Update the form in `frontend/src/pages/CustomerFormPage.tsx`
7. Update the table columns in `frontend/src/pages/CustomerListPage.tsx`
8. Regenerate Swagger docs

**Adding a new API endpoint:**
1. Create or update handler function in `backend/handlers/` with Swagger annotations
2. Add business logic in `backend/services/`
3. Add data access in `backend/repositories/` if needed
4. Register the route in `backend/routes/routes.go`
5. Add frontend API function in `frontend/src/api/`
6. Regenerate Swagger docs

**Adding a new entity:**
Follow the existing pattern: model → repository → service → handler → route. Each entity has its own file in each layer. Reference `customer` as the simplest complete example.
