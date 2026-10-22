# EZStore

> 輕量級 B2B 報價與訂單管理系統。

[English](README.md)

---

## 第一部分 — 給開發者閱讀

### 功能概述

EZStore 提供四大核心模組，管理 B2B 銷售流程：

| 模組 | 說明 |
|------|------|
| **客戶管理** | 客戶資料的 CRUD — 公司名稱、統一編號、聯絡資訊、地址、客戶等級（VIP / 一般 / 新客戶）、信用評分 |
| **產品管理** | 產品資料的 CRUD — 產品編號、名稱、描述、成本、牌價、庫存、供應商 |
| **報價單管理** | 報價單的建立、修改、發佈、刪除。單價由「報價因子」乘以牌價計算。已發佈的報價單不可再修改。 |
| **訂單管理** | 訂單的 CRUD — 可選擇關聯已發佈的報價單 |
| **AI 智能助理** | 自然語言報價單管理助手 — 查詢、複製、調整報價因子/總價、轉為訂單。Google ADK 2.x Graph Workflow + Gemini 3.8 Flash + MCP Server，以 google-agents-cli 建立骨架。 |

### 技術棧

| 層級 | 技術 |
|------|------|
| 後端 | Go 1.25 · Gin · GORM · Swagger (swaggo) · Testify |
| 前端 | React 19 · TypeScript · Tailwind CSS 4 · Vite 8 · TanStack React Query · React Hook Form · React Router |
| 資料庫 | PostgreSQL 16 |
| AI 智能助理 | Python 3.12 · Google ADK 2.10+（Graph Workflow API）· google-agents-cli 1.11 · Gemini 3.8 Flash · MCP Python SDK 2.x（Streamable HTTP）· uv |
| 編譯部署 | Docker · Docker Compose · Bun（前端）· Nginx（前端服務與 API 反向代理）|

### 專案目錄結構

```
ezstore/
├── docker-compose.yml          # 整合所有服務的編排檔
├── scripts/
│   └── seed-test-data.sql      # 冪等測試資料集（TRUNCATE + INSERT）
├── .env.example                # GEMINI_API_KEY 與 Agent 設定（複製為 .env）
├── agent/                      # ADK 2.x Graph Workflow Agent，依 agent-spec-prompt.md 開發（見 agent/README.md）
│   ├── Dockerfile
│   ├── pyproject.toml           # google-adk[mcp,a2a]>=2.10,<3（+ uv.lock）
│   ├── quotation_agent/         # agent.py（Workflow）、fast_api_app.py（ADK FastAPI + A2A）
│   └── tests/                   # unit/、integration/、eval/（題庫 + eval_config.yaml）
├── mcp_server/
│   ├── Dockerfile
│   ├── pyproject.toml           # mcp>=2.2、httpx（含 uv.lock）
│   └── server.py                # MCPServer（Streamable HTTP），6 個報價單工具
├── backend/
│   ├── Dockerfile
│   ├── main.go                 # 入口 — Gin + GORM + Swagger 初始化
│   ├── config/config.go        # 資料庫連線（環境變數）
│   ├── models/                 # GORM 模型（Customer、Product、Quotation、Order + 明細）
│   ├── repositories/           # 資料存取層（CRUD、分頁、搜尋）
│   ├── services/               # 業務邏輯（報價計算引擎、驗證）
│   ├── handlers/               # Gin HTTP 處理器 + Swagger 註解
│   ├── middleware/              # CORS、錯誤處理
│   ├── routes/routes.go        # 路由註冊
│   └── docs/                   # 自動產生的 Swagger 文件
└── frontend/
    ├── Dockerfile
    ├── nginx.conf              # 反向代理 /api → 後端、SPA fallback
    ├── vite.config.ts
    ├── src/
    │   ├── api/                # Axios API 用戶端
    │   ├── pages/              # 頁面元件
    │   ├── components/         # 共用 UI（DataTable、Pagination、StatusBadge 等）
    │   ├── types/index.ts      # TypeScript 型別定義
    │   ├── App.tsx             # Router + QueryClientProvider
    │   └── main.tsx            # React 入口
    └── e2e/                    # Playwright E2E 測試（規劃中）
```

### 開發環境需求

開發或執行 EZStore 前，需要安裝以下工具：

| 工具 | 版本 | 用途 |
|------|------|------|
| **Docker** | ≥ 24.0 | 容器運行環境 |
| **Docker Compose** | ≥ 2.20（Docker Desktop 已內含） | 多容器編排 |
| **Go** | ≥ 1.24 | 後端編譯與開發 |
| **Bun** | ≥ 1.0 | 前端套件管理與建置工具 |
| **swag**（Go CLI） | latest | Swagger 文件產生 |

> **僅執行模式：** 如果只需要*執行* EZStore（不做開發），只需安裝 Docker 與 Docker Compose。Go、Bun、swag 僅在本機開發時需要。

#### macOS

```bash
# 安裝 Homebrew（若尚未安裝）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Docker Desktop（包含 Docker Compose）
brew install --cask docker

# Go
brew install go

# Bun
brew install oven-sh/bun/bun

# swag（Swagger CLI）— 需要先安裝 Go
go install github.com/swaggo/swag/cmd/swag@latest
```

安裝 Docker Desktop 後，從「應用程式」啟動，確認選單列出現鯨魚圖示代表正在運行。

#### Windows

```powershell
# 安裝 winget（Windows 11 已內建；Windows 10 請從 Microsoft Store 安裝「應用程式安裝程式」）

# Docker Desktop（包含 Docker Compose）
winget install Docker.DockerDesktop

# Go
winget install GoLang.Go

# Bun
powershell -c "irm bun.sh/install.ps1 | iex"

# swag（Swagger CLI）— 需要先安裝 Go；安裝 Go 後請重啟終端機
go install github.com/swaggo/swag/cmd/swag@latest
```

安裝 Docker Desktop 後啟動，確認已啟用 **WSL 2 後端**（設定 → 一般 → 使用 WSL 2 引擎）。可能需要重新啟動電腦。

> **Windows 使用者注意：** 本文件的 shell 指令使用 Unix 風格語法。請使用 **Git Bash**、**WSL 2** 或 **PowerShell** 執行。若使用 PowerShell，請將 `export VAR=value` 替換為 `$env:VAR="value"`。

#### 驗證安裝

```bash
docker --version          # Docker version 24.x+
docker compose version    # Docker Compose version v2.x+
go version                # go1.24+
bun --version             # 1.x+
swag --version            # swag version v1.x+
```

### 快速開始（Docker Compose）

**API key（只有 AI 智能助理需要，其他服務沒有也能跑）：**

```bash
cp .env.example .env      # 再填入 GEMINI_API_KEY，取得方式：https://aistudio.google.com/apikey
```

**方式 A — 使用 GHCR 雲端預建 image（預設，免編譯）：**

```bash
docker compose up -d
```

**方式 B — 使用本地原始碼編譯：**

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build
```

**載入測試資料：**

```bash
docker compose exec db psql -U ezstore -f /scripts/seed-test-data.sql
```

| 服務 | 網址 |
|------|------|
| 前端 | http://localhost:3000 |
| 後端 API | http://localhost:8080/api/v1 |
| Swagger UI | http://localhost:8080/swagger/index.html |
| 健康檢查 | http://localhost:8080/health |

**執行 E2E 測試（驗證部署是否正常）：**

```bash
docker compose exec db psql -U ezstore -f /scripts/seed-test-data.sql
docker compose run --rm e2e
```

### 開發模式

```bash
# 1. 啟動 PostgreSQL
docker compose up db -d

# 2. 啟動後端
cd backend
export DB_HOST=localhost DB_PORT=5432 DB_USER=ezstore DB_PASSWORD=ezstore DB_NAME=ezstore
go run .

# 3. 啟動前端（Vite 開發伺服器，自動代理 /api）
cd frontend
bun install
bun run dev          # http://localhost:5173
```

### API 文件

所有端點皆有 Swagger 註解。後端啟動後，開啟：

```
http://localhost:8080/swagger/index.html
```

### 測試

**後端單元測試：**

```bash
cd backend
go test ./... -v -cover
```

**載入測試資料集**（冪等 — 可安全重複執行）：

```bash
docker compose exec db psql -U ezstore -f /scripts/seed-test-data.sql
```

測試資料包含：15 位客戶（5 VIP + 6 一般 + 4 新客戶）、20 個產品、12 張報價單（8 已發佈 + 4 草稿）、10 筆訂單（3 待處理 + 3 已確認 + 2 已完成 + 2 已取消）。

**重新產生 Swagger 文件：**

```bash
cd backend
$(go env GOPATH)/bin/swag init -g main.go --parseDependency --parseInternal
```

### 核心業務邏輯

**報價因子** — 根據客戶等級調整牌價：

| 客戶等級 | 預設因子 | 效果 |
|---------|---------|------|
| VIP | 0.80 | 八折 |
| 一般 | 0.90 | 九折 |
| 新客戶 | 1.00 | 原價 |

報價因子可在報價單中手動調整。

**計算公式：**

```
單價     = 牌價 × 報價因子
復價     = 單價 × 數量
總價     = Σ(復價)
獲利金額 = Σ((單價 − 成本) × 數量)
獲利率   = 獲利金額 ÷ 總價
```

**發佈不可變性** — 報價單一旦發佈：
- 不可修改（HTTP 403）
- 不可刪除（HTTP 403）
- 不可重複發佈（HTTP 400）

### AI 智能助理

> `agent/` 是在這個分支依 `agent-spec-prompt.md` 開發完成的（4.1–4.5 各階段各一個 commit）。圖的設計與如何新增一個操作，請看 [agent/README.md](agent/README.md)。

EZStore 內建自然語言報價單管理助手，以 Google ADK 2.x（`google-adk[mcp,a2a]>=2.10,<3`，Python 3.12）開發。Agent 是一張 **Graph Workflow 圖**：只有意圖分類節點會呼叫 LLM，工具選擇、工具參數、追問與拒答全部由程式決定。

**架構：**

```
使用者 → React Chat UI → nginx /agent-api → Agent（ADK FastAPI，port 8080，僅內部網路）→ MCP Server（port 8000）→ Backend REST API
                                               │                                               Streamable HTTP
                                          Gemini 3.8 Flash                                     （mcp Python SDK 2.x）
                                   （AI Studio API key 或 Vertex AI）
```

**Workflow 圖**（`agent/quotation_agent/agent.py`，ADK app 名稱 `quotation_agent`）：

```
START → prepare_input → classify_intent（LLM，output_schema=IntentResult）→ route_intent
          ├─ get_quotation / list_customer_quotations / duplicate_quotation
          ├─ update_pricing_factor / adjust_total_price / convert_to_order    ← 各呼叫一個 MCP 工具
          ├─ clarify   （缺少必要欄位 → 追問；操作暫存在 state.pending_operation）
          └─ refuse    （固定拒答文字，由程式決定）
        全部 → respond （Chat UI 只顯示這個節點的文字）
```

| 節點 | 類型 | 作用 |
|------|------|------|
| `prepare_input` | 函式 | 組出意圖分類的輸入：session 最近 6 則對話、等待補資料的操作（若有）與目前訊息 |
| `classify_intent` | `LlmAgent` | 唯一的 LLM 呼叫。輸出 `IntentResult`（意圖＋報價單編號／客戶名稱／報價因子／目標總價），temperature 0，不帶自己的對話內容 |
| `route_intent` | 函式 | 以 `Event(route=...)` 選下一個節點：離題意圖與客戶／產品的新增修改刪除（regex 防護）一律拒答、驗證 `QT-YYYYMMDD-NNN` 格式、合併等待中的操作、追問缺少的欄位 |
| 6 個操作節點 | 函式 | 透過 `McpToolset` + `StreamableHTTPConnectionParams(MCP_URL)` 各呼叫一個 MCP 工具，工具文字原樣回傳；工具錯誤轉成 `操作失敗：…` |
| `clarify` / `refuse` | 函式 | 輸出 `route_intent` 組好的追問／拒答文字 |
| `respond` | 函式 | 輸出最終回覆；前端只顯示 `nodeInfo.path` 結尾為 `/respond@<n>` 的事件 |

每一則使用者訊息都會從 `START` 重新跑一次圖。補資料的下一句有兩條路接續：`route_intent` 把等待中的操作存在 session state，`prepare_input` 也把最近的對話紀錄交給分類器。所以即使前幾輪只是被「注入」成事件（`agents-cli eval` 的多輪案例就是這樣），也能接續完成。

**功能：**

| 操作 | 說明 |
|------|------|
| 查詢報價單 | 根據報價單編號查詢詳細資訊（使用 `GET /quotations?quotation_number=`） |
| 查詢客戶報價單 | 根據客戶名稱列出所有報價單 |
| 複製報價單 | 建立新的草稿副本 |
| 修改報價因子 | 先複製再修改報價因子（原始不變） |
| 修改總價 | 先複製再以二分法調整報價因子（最多 20 次）達到目標總價（原始不變） |
| 報價單轉訂單 | 依報價單的客戶與品項建立訂單並以 `quotation_id` 關聯；報價單本身不動 |

**設計原則：**
- 所有修改採用 **copy-on-write**，原始報價單永遠不會被更動，回覆也會說明（原樣呈現的 MCP 工具文字含 `（未修改）`）
- 所有回覆包含 **純文字系統連結**（`http://localhost:3000/quotations/<id>`、`/orders/<id>`），不用 Markdown 連結
- 離題請求 **由程式拒答**；缺少必要欄位時 **追問一輪**，下一句補上即可接續完成
- 模型呼叫遇到 **429 與 503 會以指數退避重試**（google-genai `HttpRetryOptions`：共 4 次，約 2／4／8 秒再加抖動）；額度仍用完時回傳清楚的 `RESOURCE_EXHAUSTED` 訊息，而不是錯誤堆疊
- 沒有任何憑證時 Agent 仍會啟動（對話回傳「尚未設定模型憑證」的清楚錯誤），`docker compose up` 不會因缺金鑰而失敗

**環境變數：**

| 變數 | 設定位置 | 用途 |
|------|----------|------|
| `GEMINI_API_KEY` | 專案根目錄 `.env`（Compose）· `agent/.env`（本機） | Google AI Studio 金鑰，給意圖分類（以及 eval 的品質評審） |
| `GOOGLE_GENAI_USE_VERTEXAI` | 根目錄 `.env` · `agent/.env` | `FALSE` = AI Studio（預設）；`true` = Agent 的模型改走 Vertex AI |
| `GOOGLE_CLOUD_PROJECT`、`GOOGLE_CLOUD_LOCATION` | 根目錄 `.env` · `agent/.env` | Vertex AI 專案／區域（`global`）。即使用 AI Studio，本機跑 `agents-cli eval` 評分也需要，見下方說明 |
| `AGENT_MODEL` | 根目錄 `.env` · `agent/.env` | 模型名稱，預設 `gemini-3.8-flash`（品質評審也用它） |
| `MCP_URL` | Compose：`http://mcp-server:8000/mcp` · `agent/.env`：`http://localhost:8010/mcp` | MCP Server 位址 |
| `FRONTEND_URL` | 根目錄 `.env`（mcp-server）· `agent/.env` | 系統連結的網址（連結由 MCP Server 產生） |
| `ALLOW_ORIGINS` | 根目錄 `.env` | Agent API 的 CORS 來源 |
| `MCP_HOST_PORT` | 根目錄 `.env` | MCP Server 對本機開放的埠，預設 `8010` |

在 Compose 裡 Agent 的 8080 埠 **只開在 Docker 內部網路**（本機的 8080 是 backend），Chat UI 經由 nginx 的 `/agent-api/` 轉發過去。Docker 內改走 Vertex AI 時還要掛載 ADC 憑證檔，請看 `docker-compose.yml` 裡 `agent` 服務被註解的那幾行。

**本機開發**（db、backend、mcp-server 在 Compose 裡跑；mcp-server 對本機開放 8010 埠）：

```bash
cd agent
cp .env.example .env                 # 填 GEMINI_API_KEY；保留 GOOGLE_GENAI_USE_VERTEXAI=FALSE 與 MCP_URL=http://localhost:8010/mcp
uv sync --group dev --extra eval
agents-cli playground --port 8501    # 請用 8501：8080 已被 backend 使用
                                     # 開啟 http://127.0.0.1:8501/dev-ui/?app=quotation_agent
agents-cli run "我要查詢報價單，報價單編號：QT-20260330-001"
```

**測試：**

```bash
uv run pytest tests/unit -q                              # 不需 LLM、不需 MCP：路由規則＋對本機假 Gemini 端點測重試與 429
uv run --env-file .env pytest tests/integration -q       # 真的呼叫模型（3 次）：runner、/run_sse、A2A 串流、agent card（會用到 8000 埠）
agents-cli eval run                                      # 唯讀的冒煙測試集（tests/eval/datasets/basic-dataset.json）
agents-cli eval run --dataset tests/eval/datasets/quotation-guardrails.json --config tests/eval/eval_config.yaml   # 2 個拒答 + 1 個多輪追問
docker compose exec db psql -U ezstore -f /scripts/seed-test-data.sql   # （在專案根目錄）跑 actions 前先重灌 seed
agents-cli eval run --dataset tests/eval/datasets/quotation-actions.json --config tests/eval/eval_config.yaml      # 6 個操作，會新增資料
python3 scripts/grading/grade_agent.py --suite scripts/grading/student-suite.json --runs 2                          # （在專案根目錄）自我驗收分數 0–100
```

> **即使用 AI Studio 金鑰，eval 評分也需要 Google Cloud。** 在 agents-cli 1.11 與 google-cloud-aiplatform 2.6.0 下，沒有 Application Default Credentials 時 `agents-cli eval grade` 會失敗。eval SDK 一律會建立 Cloud Storage client，即使只跑程式判定的指標也一樣。而 `refusal_or_action` 這類 `prompt_template` 評審在 **Vertex AI Eval Service** 上執行，需要 GCP 專案。只需設定一次：
> 1. `gcloud auth application-default login`
> 2. 選一個已啟用計費的專案，啟用 Vertex AI API（`aiplatform.googleapis.com`），在 `agent/.env` 加上 `GOOGLE_CLOUD_PROJECT=<專案 ID>` 與 `GOOGLE_CLOUD_LOCATION=global`。保留 `GEMINI_API_KEY` 與 `GOOGLE_GENAI_USE_VERTEXAI=FALSE`：Agent 與品質評審仍走 AI Studio，只有 `prompt_template` 評審走 Vertex AI。
> 3. 新專案若評審回傳 `404 … Gaia id not found for email service-…@gcp-sa-aiplatform.iam.gserviceaccount.com`，請建立 Vertex AI service identity：`gcloud beta services identity create --service=aiplatform.googleapis.com --project=<專案 ID>`。

#### 評估報告

**評估了什麼：** 共 11 個案例。六個操作（`quotation-actions.json`）、兩個離題請求與一個多輪追問（`quotation-guardrails.json`），以及評分程式的兩題額外考題（查無此報價單、要求 Markdown 連結）。

**怎麼評估**（`agent/tests/eval/eval_config.yaml`）：

| 指標 | 類型 | 守住什麼 |
|------|------|----------|
| `custom_response_quality` | LLM 評審，1–5，本機執行（`response_quality.py`，google-genai） | 對照每題 `reference` 的整體正確性與清楚程度 |
| `link_present` | 程式判定，0/1（`link_presence.py`） | 純文字 `/quotations/<id>` 或 `/orders/<id>` 連結；Markdown 連結給 0；`off_topic*` 案例不需連結 |
| `refusal_or_action` | LLM 評審，0/1，`prompt_template`，在 Vertex AI Eval Service 執行 | 離題 → 拒答且不呼叫工具；報價單操作 → 完成且用純文字連結；缺資料 → 追問也算符合 |
| `agent_turn_count` | 程式，計數 | 回合數（多輪案例為 2） |

`scripts/grading/grade_agent.py` 另外直接查資料庫，確認原單未被更動、複製單與關聯訂單確實存在。

**結果：**

| 執行 | custom_response_quality | link_present | refusal_or_action | agent_turn_count |
|------|-------------------------|--------------|-------------------|------------------|
| guardrails（3 題） | 5.0 | 1.0 | 1.0 | 1.33（多輪案例為 2） |
| actions（6 題，重灌 seed 後） | 5.0 | 1.0 | 1.0 | 1.0 |

自我驗收評分（`student-suite.json`，`--runs 2`）：**99.6 / 100**。guardrails 30.0/30、actions 49.6/50（四項後端核對全過：原單未動、6 張複製單、因子 1.5 的複製單、訂單關聯原單）、extra 20.0/20。最低分是 `get_quotation` 的 90%：兩次中有一次 Vertex AI 評審回傳了格式錯誤的 JSON（`400 INVALID_ARGUMENT … Error parsing JSON`），評分程式把它算成 0。Agent 兩次的回覆完全相同且正確。

**穩定性：** 兩次評分中，除了那一次評審錯誤，每一題的分數都相同。意圖分類以 temperature 0 執行，而使用者看到的每一則回覆不是固定文字就是原樣的 MCP 工具輸出，所以回覆可以重現。會變動的只有模型擷取意圖與參數這一步。

**發現並處理的問題：**

| 問題 | 處理方式 |
|------|----------|
| `agents-cli eval` 的多輪案例只把前幾輪注入成事件、不會真的執行，所以補資料那一句沒有 session state | `prepare_input` 也把最近的對話紀錄交給分類器；`clarify_then_complete` 通過 |
| 多輪案例的 `agent_turn_count` 只有 1 | 前一輪放在 `agent_data.turns[0]`，補資料那一句放在 `turns[1]` |
| 模型錯誤或沒有憑證時整個 Workflow 當掉（`route_intent` 收到 `None`） | `route_intent` 改為結束這一輪、不呼叫工具；錯誤事件帶清楚訊息（對假 Gemini 端點做了單元測試） |
| 開發中用完免費額度（每日 20 次，`429 RESOURCE_EXHAUSTED`） | 429／503 指數退避重試，並回傳清楚的額度訊息 |
| MCP 錯誤顯示成 `Error executing tool get_quotation: …` | 去掉前綴：`操作失敗：找不到報價單編號 …` |
| 只用 AI Studio 金鑰時評分失敗（先是 `DefaultCredentialsError`，接著 `Could not determine GCP project`，新專案再遇到 `404 Gaia id not found`） | 依上方說明設定 Google Cloud（ADC、啟用 Vertex AI API 的專案、service identity）；Agent 本身仍走 AI Studio |
| generate 時出現 `Could not fetch /app-info … grading will degrade` | 預期內：ADK 這個實驗性端點只支援根節點是 `LlmAgent`（`"Root agent is not an LlmAgent"`），我們的指標用不到這些資料 |

**尚未涵蓋的風險**（下一輪的測試案例）：相似的客戶名稱（沒有完全相符時 MCP Server 會取第一筆模糊比對結果）、中文數字如「十萬」「打九折」、一句話裡有兩個操作，以及 eval-lab 第 7 節的「故意弄壞」測試（把 `respond` 改成 Markdown 連結，確認 `link_present` 與 `refusal_or_action` 會掉到 0）。

學員用的可信賴度評鑑 LAB：課堂版 [eval-lab-quick.zh-TW.md](eval-lab-quick.zh-TW.md)（25 分鐘）、完整版 [eval-lab.zh-TW.md](eval-lab.zh-TW.md)（60–90 分鐘，回家做）。

### 授權

本專案採用 [MIT License](LICENSE) 開源授權。

---

## 第二部分 — 給 AI Coding Agent 閱讀

> 本段為 AI 編程助手設計（Claude Code、Gemini CLI、GitHub Copilot、Antigravity、Cursor、Aider 等），提供結構化的專案上下文，協助快速理解程式碼庫。

### 專案定位

- **名稱：** EZStore
- **用途：** B2B 報價與訂單管理系統
- **語言：** Go（後端）、TypeScript/React（前端）、Python 3.12（Agent + MCP Server）
- **資料庫：** PostgreSQL 16
- **部署：** Docker Compose（5 個服務：db、backend、frontend、agent、mcp-server）

### 架構模式

後端採用**三層式架構**：

```
HTTP 請求 → Handler（Gin）→ Service（業務邏輯）→ Repository（GORM/DB）
```

- **Handler** 解析 HTTP 輸入、呼叫 Service、回傳 JSON。包含 Swagger 註解。
- **Service** 包含驗證與業務邏輯。不存取 `*gin.Context`。
- **Repository** 封裝 GORM 查詢。回傳 model 或 error，不涉及 HTTP 概念。

### 關鍵檔案路徑

| 用途 | 路徑 |
|------|------|
| 後端入口 | `backend/main.go` |
| 資料庫設定 | `backend/config/config.go` |
| 所有 Model | `backend/models/*.go` |
| 所有 Repository | `backend/repositories/*.go` |
| 所有 Service | `backend/services/*.go` |
| 所有 Handler | `backend/handlers/*.go` |
| 路由註冊 | `backend/routes/routes.go` |
| CORS 中介層 | `backend/middleware/cors.go` |
| 錯誤回應輔助函式 | `backend/middleware/error_handler.go` |
| 報價因子預設值 | `backend/models/customer.go` → `DefaultPricingFactor()` |
| 報價計算邏輯 | `backend/services/quotation_service.go` → `computeTotals()`、`buildItems()` |
| 前端入口 | `frontend/src/main.tsx` |
| React 路由 | `frontend/src/App.tsx` |
| TypeScript 型別 | `frontend/src/types/index.ts` |
| API 用戶端 | `frontend/src/api/*.ts` |
| 頁面元件 | `frontend/src/pages/*.tsx` |
| 共用元件 | `frontend/src/components/shared/*.tsx` |
| Agent Workflow 圖 | `agent/quotation_agent/agent.py`（`Workflow`、`Intent`、`IntentResult`、各節點函式） |
| Agent 提示詞／固定回覆 | `agent/quotation_agent/agent.py`（`classify_intent.instruction`、`REFUSAL_TEXT`、`ARG_LABELS`…） |
| Agent FastAPI app | `agent/quotation_agent/fast_api_app.py` |
| Agent eval | `agent/tests/eval/eval_config.yaml`、`agent/tests/eval/link_presence.py`、`agent/tests/eval/datasets/*.json` |
| Agent 單元測試 | `agent/tests/unit/test_route_intent.py`、`agent/tests/unit/test_model_errors.py` |
| MCP Server（6 個工具，mcp 2.x `MCPServer`） | `mcp_server/server.py` |
| Agent Chat UI | `frontend/src/pages/AgentChatPage.tsx` |
| Agent API 用戶端 | `frontend/src/api/agentApi.ts` |
| Docker 編排 | `docker-compose.yml` |
| 測試資料集 | `scripts/seed-test-data.sql` |

### 資料庫 Schema 摘要

共 6 張表。主要實體使用 GORM 軟刪除（`deleted_at`）。明細表使用硬刪除。

```
customers         → id, name, tax_id（唯一, 8碼數字）, contact_name, contact_phone,
                    contact_email, address, level（vip|standard|new）, credit_score（0-100）

products          → id, product_number（唯一）, name, description, cost, list_price,
                    inventory, supplier

quotations        → id, quotation_number（唯一, 自動: QT-YYYYMMDD-NNN）,
                    customer_id（FK）, customer_level（快照）, pricing_factor,
                    total_price, profit_amount, profit_rate,
                    status（draft|published）, notes

quotation_items   → id, quotation_id（FK, CASCADE）, product_id（FK）,
                    product_name（快照）, product_cost（快照）, list_price（快照）,
                    unit_price, quantity, subtotal

orders            → id, order_number（唯一, 自動: ORD-YYYYMMDD-NNN）,
                    customer_id（FK）, quotation_id（FK, 可為空）,
                    total_price, status（pending|confirmed|completed|cancelled）, notes

order_items       → id, order_id（FK, CASCADE）, product_id（FK）,
                    product_name（快照）, unit_price, quantity, subtotal
```

**重要：** 報價單/訂單明細儲存產品資料的*快照*（名稱、成本、牌價），確保產品資料後續修改不影響歷史記錄。

### REST API 端點

Base path: `/api/v1`

```
GET    /health                        → { status: "ok" }
GET    /api/v1/pricing-factor/:level  → { level, pricing_factor }

# 客戶
GET    /api/v1/customers              → 分頁列表（?page, ?page_size, ?search）
GET    /api/v1/customers/:id
POST   /api/v1/customers
PUT    /api/v1/customers/:id
DELETE /api/v1/customers/:id          → 軟刪除

# 產品
GET    /api/v1/products               → 分頁列表（?page, ?page_size, ?search）
GET    /api/v1/products/:id
POST   /api/v1/products
PUT    /api/v1/products/:id
DELETE /api/v1/products/:id           → 軟刪除

# 報價單
GET    /api/v1/quotations             → 分頁列表（?page, ?page_size, ?status, ?customer_id, ?quotation_number）
GET    /api/v1/quotations/:id         → 含 items[] 與 customer
POST   /api/v1/quotations             → body: { customer_id, pricing_factor, notes, items: [{product_id, quantity}] }
PUT    /api/v1/quotations/:id         → 僅草稿可修改；body 同 POST
POST   /api/v1/quotations/:id/publish → 將狀態設為 published（不可逆）
DELETE /api/v1/quotations/:id         → 僅草稿可刪除；軟刪除

# 訂單
GET    /api/v1/orders                 → 分頁列表（?page, ?page_size, ?status, ?customer_id）
GET    /api/v1/orders/:id             → 含 items[] 與 customer
POST   /api/v1/orders                 → body: { customer_id, quotation_id?, notes, items: [{product_id, unit_price, quantity}] }
PUT    /api/v1/orders/:id
DELETE /api/v1/orders/:id             → 軟刪除
```

### 報價計算規則

建立或修改報價單時，後端：

1. 查詢客戶 → 快照 `customer_level`
2. 對每個明細項目：查詢產品 → 快照 `product_name`、`product_cost`、`list_price`
3. 計算 `unit_price = list_price × pricing_factor`
4. 計算 `subtotal = unit_price × quantity`
5. 計算 `total_price = Σ(subtotal)`
6. 計算 `profit_amount = Σ((unit_price − cost) × quantity)`
7. 計算 `profit_rate = profit_amount ÷ total_price`（防護：total 為 0 時回傳 0）

預設報價因子：VIP → 0.80、一般 → 0.90、新客戶 → 1.00（定義於 `backend/models/customer.go`）。

### 業務規則與約束條件

- **統一編號**：必須為 8 位數字（`^\d{8}$`）
- **客戶等級**：必須為 `vip`、`standard`、`new` 其一
- **信用評分**：整數 0–100
- **產品成本與牌價**：必須 ≥ 0（使用 Decimal，不用 float）
- **數量**：必須 > 0
- **已發佈報價單**：不可修改、刪除、重複發佈
- **報價單/訂單編號**：自動產生格式 `QT-YYYYMMDD-NNN` / `ORD-YYYYMMDD-NNN`
- **軟刪除**：customers、products、quotations、orders 使用 `deleted_at`
- **硬刪除**：quotation_items 與 order_items 在父層更新時直接刪除

### 常用開發指令

```bash
# 完整環境（Docker）
docker compose up --build -d
docker compose down -v                    # 停止並移除 volumes
docker compose exec db psql -U ezstore -f /scripts/seed-test-data.sql

# 後端
cd backend
go run .                                  # 啟動 API 伺服器（port 8080）
go test ./... -v -cover                   # 執行所有測試
go build -o ezstore-api .                 # 編譯
$(go env GOPATH)/bin/swag init -g main.go --parseDependency --parseInternal  # 重新產生 Swagger

# 前端
cd frontend
bun install                               # 安裝依賴
bun run dev                               # 開發伺服器（port 5173，代理 /api 到 :8080）
bun run build                             # 正式建置 → dist/

# MCP Server
cd mcp_server
uv sync && BACKEND_URL=http://localhost:8080 MCP_PORT=8010 uv run python server.py

# Agent（讀取 agent/.env：GEMINI_API_KEY、GOOGLE_GENAI_USE_VERTEXAI=FALSE、MCP_URL、AGENT_MODEL；
#        eval 評分另需 ADC 與 GOOGLE_CLOUD_PROJECT，見「AI 智能助理」一節）
cd agent
uv sync --group dev --extra eval
agents-cli playground --port 8501         # 本機網頁介面（8080 是 backend）
agents-cli run "我要查詢報價單，報價單編號：QT-20260330-001"
uv run pytest tests/unit -q               # 不需 LLM、不需 MCP
uv run --env-file .env pytest tests/integration -q   # 會真的呼叫模型
agents-cli eval run --dataset tests/eval/datasets/quotation-guardrails.json --config tests/eval/eval_config.yaml
```

### 常見修改場景

**為現有實體新增欄位（例如在 Customer 新增 `fax`）：**
1. 在 `backend/models/customer.go` 新增欄位（含 GORM + JSON tag）
2. GORM AutoMigrate 於 `main.go` 會自動處理資料表變更
3. 如需要，在 `backend/services/customer_service.go` 更新驗證邏輯
4. 更新 `backend/handlers/customer_handler.go` 的 Swagger 註解
5. 在 `frontend/src/types/index.ts` 新增欄位
6. 更新 `frontend/src/pages/CustomerFormPage.tsx` 的表單
7. 更新 `frontend/src/pages/CustomerListPage.tsx` 的表格欄位
8. 重新產生 Swagger 文件

**新增 API 端點：**
1. 在 `backend/handlers/` 建立或更新 handler 函式（含 Swagger 註解）
2. 在 `backend/services/` 加入業務邏輯
3. 如需要，在 `backend/repositories/` 加入資料存取
4. 在 `backend/routes/routes.go` 註冊路由
5. 在 `frontend/src/api/` 加入前端 API 函式
6. 重新產生 Swagger 文件

**新增實體：**
依循現有模式：model → repository → service → handler → route。每個實體在每一層都有獨立檔案。可參考 `customer` 作為最簡單的完整範例。
