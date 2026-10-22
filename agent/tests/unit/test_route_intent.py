"""route_intent 的程式路由規則（不呼叫 LLM、不連 MCP Server）。"""

from types import SimpleNamespace

from quotation_agent.agent import (
    PENDING_KEY,
    REFUSAL_TEXT,
    Intent,
    IntentResult,
    route_intent,
)


def _route(user_text: str, result: IntentResult, pending: dict | None = None):
    state = {"last_user_message": user_text, PENDING_KEY: pending}
    return route_intent(SimpleNamespace(state=state), result)


def test_operation_routes_to_tool_node_with_args() -> None:
    event = _route(
        "我要修改報價單報價因子，報價單編號：QT-20260330-001，報價因子改為 1.5",
        IntentResult(
            intent=Intent.UPDATE_PRICING_FACTOR,
            quotation_number="QT-20260330-001",
            new_pricing_factor=1.5,
        ),
    )
    assert event.actions.route == "update_pricing_factor"
    assert event.output == {
        "quotation_number": "QT-20260330-001",
        "new_pricing_factor": 1.5,
    }


def test_off_topic_is_refused() -> None:
    event = _route("今天天氣如何？", IntentResult(intent=Intent.OFF_TOPIC))
    assert event.actions.route == "refuse"
    assert event.output == REFUSAL_TEXT


def test_customer_crud_is_refused_even_if_misclassified() -> None:
    event = _route(
        "幫我新增一個客戶叫復仇者聯盟",
        IntentResult(
            intent=Intent.LIST_CUSTOMER_QUOTATIONS, customer_name="復仇者聯盟"
        ),
    )
    assert event.actions.route == "refuse"


def test_missing_quotation_number_asks_and_remembers_operation() -> None:
    event = _route("我要將報價單轉訂單", IntentResult(intent=Intent.CONVERT_TO_ORDER))
    assert event.actions.route == "clarify"
    assert event.output.startswith("請提供報價單編號")
    assert event.actions.state_delta[PENDING_KEY]["intent"] == "convert_to_order"


def test_follow_up_completes_pending_operation() -> None:
    event = _route(
        "QT-20260330-001",
        IntentResult(intent=Intent.UNCLEAR, quotation_number="QT-20260330-001"),
        pending={"intent": "convert_to_order", "args": {}},
    )
    assert event.actions.route == "convert_to_order"
    assert event.output == {"quotation_number": "QT-20260330-001"}
    assert event.actions.state_delta[PENDING_KEY] is None


def test_invented_quotation_number_format_is_rejected() -> None:
    event = _route(
        "我要複製報價單",
        IntentResult(intent=Intent.DUPLICATE_QUOTATION, quotation_number="12"),
    )
    assert event.actions.route == "clarify"
