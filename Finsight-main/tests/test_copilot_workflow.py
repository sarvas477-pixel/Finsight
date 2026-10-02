from src.ai import ask_gemini, build_chat_prompt, is_chart_request
from src.copilot_workflow import copilot_workflow


def test_open_ended_questions_are_not_scope_guarded():
    for question in (
        "what's the weather today",
        "send money to my friend",
        "explain quantum physics",
        "what is an app",
    ):
        answer, mode = ask_gemini(question, [], [])
        assert mode != "scope_guard"
        assert answer


def test_workflow_returns_structured_ai_result():
    result = copilot_workflow("hi", [], [])
    assert result["stage"] == "ai_result"
    assert result["mode"] != "scope_guard"
    assert result["answer"]


def test_invoice_context_is_not_guarded():
    answer, mode = ask_gemini("why is INV003 flagged?", [], [])
    assert mode != "scope_guard"
    assert answer
    assert "invoice" in answer.lower() or "dataset" in answer.lower()


def test_trusted_payload_contains_invoice_fields():
    results = [{
        "invoice_id": "INV001",
        "status": "CLEAN",
        "route": "AUTO_PASS",
        "confidence": 1.0,
        "human_review_required": False,
        "rule_ids": [],
        "reasons": [],
        "evidence": {
            "invoice_id": "INV001",
            "vendor": "ABC Suppliers",
            "amount": 4500.0,
            "category": "Travel",
            "invoice_date": "2026-09-14",
        },
    }]
    prompt = build_chat_prompt("show vendor and amount", results)
    assert "ABC Suppliers" in prompt
    assert "4500.0" in prompt
    assert "Travel" in prompt
    assert "2026-09-14" in prompt


def test_chart_request_is_detected():
    assert is_chart_request("give me the result in graph")
