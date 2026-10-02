from src.ai import ask_gemini
from src.copilot_workflow import copilot_workflow

def test_unrelated_question_does_not_use_gemini():
    answer,mode=ask_gemini("what's the weather today",[],[])
    assert mode=="scope_guard" and "cannot help" in answer.lower()

def test_external_action_is_guarded():
    answer,mode=ask_gemini("send money to my friend",[],[])
    assert mode=="scope_guard" and "cannot help" in answer.lower()

def test_general_question_is_out_of_scope():
    answer,mode=ask_gemini("explain quantum physics",[],[])
    assert mode=="scope_guard" and "cannot help" in answer.lower()

def test_workflow_returns_structured_ai_result():
    result=copilot_workflow("hi",[],[])
    assert result["stage"]=="ai_result" and result["mode"]=="deterministic" and result["answer"]

def test_unrelated_generic_words_are_guarded():
    answer,mode=ask_gemini("what is an app",[],[])
    assert mode=="scope_guard" and "cannot help" in answer.lower()

def test_invoice_context_is_not_guarded():
    answer,mode=ask_gemini("why is INV003 flagged?",[],[])
    assert mode in {"template_fallback","deterministic"}
    assert "invoice" in answer.lower() or "dataset" in answer.lower()
