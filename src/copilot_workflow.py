"""FinSight Copilot workflow orchestration.

Pipeline:
    invoice CSV -> deterministic Python rule engine -> trusted analysis -> AI explanation

The AI layer never changes the deterministic invoice decision.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.rule_engine import process_invoices, summarize_results
from src.ai import ask_gemini


def analyze_invoice_workflow(df: pd.DataFrame) -> dict[str, Any]:
    """Run the authoritative Python invoice analysis and return a structured result."""
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
) -> dict[str, Any]:
    """Route a question through deterministic context first, then the AI layer."""
    answer, mode = ask_gemini(question, results, conversation)
    return {
        "stage": "ai_result",
        "answer": answer,
        "mode": mode,
        "invoice_context_loaded": bool(results),
        "decision_source": "python_rule_engine" if results else None,
    }


def full_workflow(
    df: pd.DataFrame,
    question: str | None = None,
    conversation: list[Any] | None = None,
) -> dict[str, Any]:
    """Run the complete invoice -> Python -> AI workflow."""
    analysis = analyze_invoice_workflow(df)
    response = None
    if question:
        response = copilot_workflow(question, analysis["results"], conversation)
    return {
        "analysis": analysis,
        "response": response,
    }
