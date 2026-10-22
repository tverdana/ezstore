# EZStore 報價單管理 Agent（`agent/`）

[English below](#english)

以 Google ADK 2.x 的 Graph Workflow API（`google.adk.workflow.Workflow`）建成的報價單管理助手。骨架由 `agents-cli scaffold create`（agents-cli 1.11）產生，ADK app 名稱是 `quotation_agent`。整體架構、環境變數與評估結果請看專案根目錄的 [README](../README.zh-TW.md#ai-智能助理)。

## 圖的設計

```
START → prepare_input → classify_intent（LLM）→ route_intent ─┬─ get_quotation ────────────┐
                                                             ├─ list_customer_quotations ─┤
                                                             ├─ duplicate_quotation ──────┤
                                                             ├─ update_pricing_factor ────┼→ respond
                                                             ├─ adjust_total_price ───────┤
                                                             ├─ convert_to_order ─────────┤
                                                             ├─ clarify（追問）───────────┤
                                                             └─ refuse（拒答）────────────┘
```

全部定義在 [`quotation_agent/agent.py`](quotation_agent/agent.py)。

| 節點 | 輸入 → 輸出 | 說明 |
|------|-------------|------|
| `prepare_input` | 使用者訊息（`types.Content`）→ 文字 | 把 session 最近 6 則對話、等待補資料的操作（`state.pending_operation`）與目前訊息組成分類器的輸入，並把目前訊息存進 `state.last_user_message` |
| `classify_intent` | 文字 → `IntentResult` | **唯一呼叫 LLM 的節點**。`LlmAgent`，`output_schema=IntentResult`、`include_contents="none"`（只看 `prepare_input` 給的內容）、temperature 0 |
| `route_intent` | `IntentResult` → `Event(route=…)` | 程式決定路由：離題意圖或客戶／產品的新增修改刪除（regex）→ `refuse`；缺欄位 → `clarify` 並記住操作；欄位齊全 → 對應的操作節點，並帶上工具參數 |
| 6 個操作節點 | 工具參數（dict）→ 文字 | 每個節點只呼叫一個同名的 MCP 工具（`_call_mcp_tool`），工具文字原樣回傳；工具錯誤轉成 `操作失敗：…` |
| `clarify`、`refuse` | 文字 → 文字 | 輸出 `route_intent` 組好的追問句或固定拒答文字 |
| `respond` | 文字 → 回覆 | 最終回覆，送出 `content` 事件 |

設計重點：

- **LLM 只做分類與擷取參數。** 要呼叫哪個工具、帶什麼參數、要不要追問或拒答，全部由 `route_intent` 的程式決定；報價單編號以 `QT-\d{8}-\d{3}` 驗證，目前訊息裡有編號時以它為準。
- **拒答是程式邏輯。** 離題由 `route_intent` 路由到 `refuse`，回覆是固定的 `REFUSAL_TEXT`，不經 LLM 產生；另有 regex 防護，客戶／產品的新增修改刪除即使被誤判成報價單操作也會拒答。
- **追問後接續。** 缺欄位時把操作與已知參數存在 `state.pending_operation`；下一句只補資料時（分類為 `unclear` 或同一操作）就合併參數完成。`prepare_input` 同時把對話紀錄交給分類器，所以即使前幾輪只是被注入成事件、沒有 state（`agents-cli eval` 的多輪案例），也能接續。
- **回覆原樣呈現工具文字。** MCP 工具已經附上純文字系統連結，修改類操作也已註明原始報價單「未修改」，Agent 不改寫，也不會產生 Markdown 連結。
- **與前端的約定。** 前端只顯示 `nodeInfo.path` 結尾為 `/respond@<n>` 的事件，所以最終回覆一定要由叫做 `respond` 的節點送出；App 名稱必須是 `quotation_agent`。
- **錯誤處理。** 模型呼叫對 429／503 以指數退避重試（`MODEL_RETRY_OPTIONS`）；重試用盡或沒有憑證時，`classify_intent` 的 callback 送出清楚的錯誤訊息，`route_intent` 收到 `None` 就結束這一輪、不呼叫工具。

## 如何新增一個操作

以新增「刪除草稿報價單」（MCP 工具 `delete_quotation(quotation_number)`）為例：

1. **MCP 工具**：在 `mcp_server/server.py` 新增工具（MCP Server 是另一個元件，修改前請先確認）。Agent 會透過 `tool_filter` 只載入 `REQUIRED_ARGS` 裡列出的工具。
2. **意圖**：在 `Intent` 加上 `DELETE_QUOTATION = "delete_quotation"`，值必須和 MCP 工具名稱相同。
3. **參數**：在 `REQUIRED_ARGS` 加上 `Intent.DELETE_QUOTATION: ["quotation_number"]`（依追問順序列出），在 `OPERATION_LABELS` 加上中文名稱「刪除報價單」。若需要新的參數，在 `IntentResult` 加欄位，並在 `ARG_LABELS` 加上追問用的說明。
4. **分類提示詞**：在 `classify_intent` 的 `instruction` 的 intent 清單加上一行 `delete_quotation：刪除草稿報價單`。
5. **操作節點**：
   ```python
   async def delete_quotation(ctx: Context, node_input: dict) -> str:
       return await _call_mcp_tool(ctx, "delete_quotation", node_input)
   ```
6. **接上圖**：在 `OPERATION_NODES` 加上 `Intent.DELETE_QUOTATION.value: delete_quotation`。路由邊與到 `respond` 的邊都由 `OPERATION_NODES` 產生，不用再改 `edges`。
7. **測試**：在 `tests/unit/test_route_intent.py` 加一個路由測試（不需 LLM）；在 `tests/eval/datasets/quotation-actions.json` 加一個 `eval_case_id` 為 `delete_quotation` 的案例。若操作會改資料，跑 eval 前先重灌 seed。
8. **驗證**：`uv run pytest tests/unit -q`、`agents-cli run "我要刪除報價單，報價單編號：…"`、`agents-cli eval run --dataset tests/eval/datasets/quotation-actions.json --config tests/eval/eval_config.yaml`。

## 開發指令

```bash
cp .env.example .env                 # 填 GEMINI_API_KEY；MCP_URL=http://localhost:8010/mcp
uv sync --group dev --extra eval
agents-cli playground --port 8501    # 8080 是 backend；開 http://127.0.0.1:8501/dev-ui/?app=quotation_agent
agents-cli run "我要查詢報價單，報價單編號：QT-20260330-001"
uv run pytest tests/unit -q          # 不需 LLM、不需 MCP
uv run --env-file .env pytest tests/integration -q
agents-cli eval run --dataset tests/eval/datasets/quotation-guardrails.json --config tests/eval/eval_config.yaml
```

`agents-cli eval` 的評分即使用 AI Studio 金鑰也需要 ADC 與啟用 Vertex AI API 的 GCP 專案（`GOOGLE_CLOUD_PROJECT`），設定方式見[根目錄 README](../README.zh-TW.md#ai-智能助理)。

| 路徑 | 內容 |
|------|------|
| `quotation_agent/agent.py` | Workflow、節點、分類提示詞、固定回覆文字、重試設定 |
| `quotation_agent/fast_api_app.py` | ADK FastAPI app（`/run_sse`、sessions）與 A2A 路由，容器以 uvicorn 啟動 |
| `tests/unit/` | 路由規則；用本機假 Gemini 端點測重試、429、沒有憑證 |
| `tests/integration/` | scaffold 的整合測試（會真的呼叫模型） |
| `tests/eval/` | 題庫、`eval_config.yaml`、`link_presence.py`、`response_quality.py` |
| `Dockerfile` | `uv sync --frozen --no-dev`、`/list-apps` 健康檢查、port 8080 |

---

## English

Quotation-management agent built with the Google ADK 2.x graph Workflow API (`google.adk.workflow.Workflow`), scaffolded with `agents-cli scaffold create` (agents-cli 1.11); ADK app name `quotation_agent`. Architecture, environment variables and evaluation results are in the root [README](../README.md#ai-agent).

**Graph design** (all in [`quotation_agent/agent.py`](quotation_agent/agent.py)): `START → prepare_input → classify_intent → route_intent → {6 operation nodes | clarify | refuse} → respond`.

- `prepare_input` builds the classifier input from the last 6 messages of session history, the pending operation and the current message.
- `classify_intent` is the **only LLM call**: an `LlmAgent` with `output_schema=IntentResult`, `include_contents="none"` and temperature 0.
- `route_intent` decides in code. Off-topic intents and customer/product CRUD requests (regex guard) go to `refuse`, which returns fixed text. Missing fields go to `clarify`, and the operation is kept in `state.pending_operation` so the next message can complete it. Otherwise it routes to the operation node with the tool arguments, after validating the quotation number format.
- Each operation node calls exactly one MCP tool of the same name and returns its text unchanged, so links stay plain text and 「未修改」 is preserved. Tool errors become `操作失敗：…`.
- `respond` emits the final reply. The frontend only shows events whose `nodeInfo.path` ends in `/respond@<n>`, so the node must keep that name.
- Model calls retry 429/503 with exponential backoff. After retries, or without credentials, a callback emits a clear error and `route_intent` ends the turn without calling tools.

**Adding an operation** (example: MCP tool `delete_quotation(quotation_number)`):

1. Add the tool to `mcp_server/server.py` (separate component; confirm before changing it).
2. Add `Intent.DELETE_QUOTATION = "delete_quotation"` (value = MCP tool name).
3. Add its required arguments to `REQUIRED_ARGS` and a label to `OPERATION_LABELS`. New parameters also need an `IntentResult` field and an `ARG_LABELS` entry.
4. Describe the intent in `classify_intent.instruction`.
5. Add the node: `async def delete_quotation(ctx, node_input): return await _call_mcp_tool(ctx, "delete_quotation", node_input)`.
6. Register it in `OPERATION_NODES`. The edges and the MCP `tool_filter` are derived from it.
7. Add a routing unit test and an eval case with `eval_case_id` = `delete_quotation`. Reseed before running evals that change data.
8. Verify with `uv run pytest tests/unit -q`, `agents-cli run "…"` and `agents-cli eval run …`.

**Commands:** see above. Run the playground with `agents-cli playground --port 8501` (port 8080 is the backend). `agents-cli eval` grading needs ADC and a GCP project with the Vertex AI API (`GOOGLE_CLOUD_PROJECT`) even with an AI Studio key; see the root README.
