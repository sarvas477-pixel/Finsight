"""FinSight Copilot orchestration.

The workflow retrieves deterministic evidence before asking the language model
for a response. The model explains trusted evidence; it is not the decision
engine.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from src.ai import ask_gemini, generate_gemini_chart, is_chart_request
from src.copilot_tools import build_tool_context
from src.rule_engine import process_invoices, summarize_results


def analyze_invoice_workflow(df: pd.DataFrame) -> dict[str, Any]:
    results = process_invoices(df)
    return {
        "stage": "python_analysis",
        "results": results,
        "summary": summarize_results(results),
    }


def copilot_workflow(
    question: str,
    results: list[dict[str, Any]] | None,
    conversation: list[Any] | None = None,
    current_invoice_id: str | None = None,
) -> dict[str, Any]:
    """Run retrieval/tooling first, then produce an evidence-grounded answer."""
    tool_context = build_tool_context(
        question,
        results,
        current_invoice_id=current_invoice_id,
    )
    answer, mode = ask_gemini(
        question,
        results,
        conversation,
        tool_context=tool_context,
    )
    chart = None
    chart_mode = None
    if is_chart_request(question):
        chart, chart_mode = generate_gemini_chart(
            question,
            results,
            conversation,
            tool_context=tool_context,
        )
    return {
        "stage": "ai_result",
        "answer": answer,
        "mode": mode,
        "chart": chart,
        "chart_mode": chart_mode,
        "tool_context": tool_context,
        "invoice_context_loaded": bool(results),
        "current_invoice_id": current_invoice_id,
        "decision_source": "python_rule_engine" if results else None,
    }


def full_workflow(
    df: pd.DataFrame,
    question: str | None = None,
    conversation: list[Any] | None = None,
    current_invoice_id: str | None = None,
) -> dict[str, Any]:
    analysis = analyze_invoice_workflow(df)
    response = (
        copilot_workflow(
            question,
            analysis["results"],
            conversation,
            current_invoice_id=current_invoice_id,
        )
        if question
        else None
    )
    return {"analysis": analysis, "response": response}
