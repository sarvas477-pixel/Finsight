"""FinSight Copilot orchestration."""
from __future__ import annotations
from typing import Any
import pandas as pd
from src.ai import ask_gemini
from src.rule_engine import process_invoices, summarize_results

def analyze_invoice_workflow(df: pd.DataFrame) -> dict[str, Any]:
    results = process_invoices(df)
    return {"stage":"python_analysis","results":results,"summary":summarize_results(results)}

def copilot_workflow(question: str, results: list[dict[str, Any]] | None,
                     conversation: list[Any] | None = None) -> dict[str, Any]:
    answer, mode = ask_gemini(question, results, conversation)
    return {"stage":"ai_result","answer":answer,"mode":mode,
            "invoice_context_loaded":bool(results),
            "decision_source":"python_rule_engine" if results else None}

def full_workflow(df: pd.DataFrame, question: str | None = None,
                  conversation: list[Any] | None = None) -> dict[str, Any]:
    analysis = analyze_invoice_workflow(df)
    response = copilot_workflow(question, analysis["results"], conversation) if question else None
    return {"analysis":analysis,"response":response}
