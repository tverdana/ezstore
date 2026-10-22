"""模型呼叫的重試與錯誤訊息（用本機假 Gemini 端點，不呼叫真正的模型）。"""

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from google.adk.models import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from quotation_agent import agent as agent_module
from quotation_agent.agent import (
    MISSING_CREDENTIALS_TEXT,
    MODEL,
    MODEL_RETRY_OPTIONS,
    QUOTA_EXHAUSTED_TEXT,
    REFUSAL_TEXT,
    app,
    classify_intent,
    root_agent,
)

_OFF_TOPIC = {
    "candidates": [
        {
            "content": {
                "role": "model",
                "parts": [{"text": '{"intent": "off_topic"}'}],
            },
            "finishReason": "STOP",
        }
    ]
}


def _error(code: int, status: str) -> dict:
    return {"error": {"code": code, "message": status, "status": status}}


class _FakeGemini(ThreadingHTTPServer):
    """依序回傳預先排好的 (HTTP 狀態碼, JSON) 回應，並記錄收到幾次請求。"""

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.script: list[tuple[int, dict]] = []
        self.paths: list[str] = []

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}"


class _Handler(BaseHTTPRequestHandler):
    server: _FakeGemini

    def do_POST(self) -> None:
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.server.paths.append(self.path)
        status, body = self.server.script.pop(0)
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args) -> None:
        pass


@pytest.fixture
def fake_gemini(monkeypatch: pytest.MonkeyPatch) -> Iterator[_FakeGemini]:
    server = _FakeGemini()
    threading.Thread(target=server.serve_forever, daemon=True).start()

    monkeypatch.setenv("GEMINI_API_KEY", "test-dummy-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-dummy-key")
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_USE_ENTERPRISE", raising=False)
    # 次數與狀態碼沿用正式設定，只把等待時間縮短，讓測試跑得快
    fast_retry = MODEL_RETRY_OPTIONS.model_copy(
        update={"initial_delay": 0.01, "max_delay": 0.05, "jitter": 0.01}
    )
    fake_model = Gemini(model=MODEL, base_url=server.url, retry_options=fast_retry)
    # Workflow 建圖時會複製 LlmAgent，要換的是圖裡那個節點的 model
    graph_node = next(
        n for n in root_agent._require_graph().nodes if n.name == classify_intent.name
    )
    monkeypatch.setattr(graph_node, "model", fake_model)
    # 防呆：確認實際會用到的 client 指向假端點，絕不打到真正的 Gemini API
    base_url = fake_model.api_client._api_client._http_options.base_url
    assert base_url.startswith(server.url), base_url
    yield server
    server.shutdown()


async def _run(message: str) -> list:
    runner = Runner(app=app, session_service=InMemorySessionService())
    session = await runner.session_service.create_session(
        app_name=app.name, user_id="test_user"
    )
    return [
        event
        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part(text=message)]),
        )
    ]


def _respond_text(events: list) -> str:
    for event in events:
        if event.node_info.path.endswith(("/respond@1",)) and event.content:
            return "".join(p.text or "" for p in event.content.parts)
    return ""


def test_retry_only_429_and_503_with_exponential_backoff() -> None:
    assert MODEL_RETRY_OPTIONS.http_status_codes == [429, 503]
    assert MODEL_RETRY_OPTIONS.attempts == 4
    assert MODEL_RETRY_OPTIONS.exp_base == 2.0
    assert MODEL_RETRY_OPTIONS.initial_delay == 2.0
    assert agent_module.classify_intent.on_model_error_callback is not None


@pytest.mark.asyncio
async def test_503_is_retried_then_succeeds(fake_gemini: _FakeGemini) -> None:
    fake_gemini.script = [
        (503, _error(503, "UNAVAILABLE")),
        (503, _error(503, "UNAVAILABLE")),
        (200, _OFF_TOPIC),
    ]
    events = await _run("今天天氣如何？")

    assert len(fake_gemini.paths) == 3
    assert all(":generateContent" in p for p in fake_gemini.paths)
    assert _respond_text(events) == REFUSAL_TEXT
    assert not any(e.error_message for e in events)


@pytest.mark.asyncio
async def test_429_after_retries_gives_clear_message(fake_gemini: _FakeGemini) -> None:
    fake_gemini.script = [(429, _error(429, "RESOURCE_EXHAUSTED"))] * 4
    events = await _run("我要查詢報價單，報價單編號：QT-20260330-001")

    assert len(fake_gemini.paths) == MODEL_RETRY_OPTIONS.attempts
    errors = [e for e in events if e.error_message]
    assert errors, "429 應該回報錯誤事件"
    assert errors[-1].error_code == "RESOURCE_EXHAUSTED"
    assert errors[-1].error_message == QUOTA_EXHAUSTED_TEXT
    assert _respond_text(events) == ""


@pytest.mark.asyncio
async def test_missing_credentials_gives_clear_message(
    fake_gemini: _FakeGemini, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY")
    monkeypatch.delenv("GOOGLE_API_KEY")
    events = await _run("我要查詢報價單，報價單編號：QT-20260330-001")

    assert fake_gemini.paths == []
    errors = [e for e in events if e.error_message]
    assert errors[-1].error_code == "MISSING_CREDENTIALS"
    assert errors[-1].error_message == MISSING_CREDENTIALS_TEXT
    assert _respond_text(events) == ""


@pytest.mark.asyncio
async def test_400_is_not_retried(fake_gemini: _FakeGemini) -> None:
    fake_gemini.script = [(400, _error(400, "INVALID_ARGUMENT"))]
    with pytest.raises(Exception, match="400"):
        await _run("今天天氣如何？")
    assert len(fake_gemini.paths) == 1
