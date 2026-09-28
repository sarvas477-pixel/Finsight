from src.ai import ask_gemini
from src.copilot_workflow import copilot_workflow


def test_unrelated_question_does_not_use_gemini():
    answer, mode = ask_gemini("what's the weather today", [], [])
    assert mode == "scope_guard"
    assert "cannot help" in answer.lower()


def test_external_action_is_guarded():
    answer, mode = ask_gemini("send money to my friend", [], [])
    assert mode == "scope_guard"
    assert "cannot help" in answer.lower()


def test_general_question_is_out_of_scope():
    answer, mode = ask_gemini("explain quantum physics", [], [])
    assert mode == "scope_guard"
    assert "cannot help" in answer.lower()


def test_workflow_returns_structured_ai_result():
    result = copilot_workflow("hi", [], [])
    assert result["stage"] == "ai_result"
    assert result["mode"] == "deterministic"
    assert result["answer"]
