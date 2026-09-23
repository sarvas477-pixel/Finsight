"""Single invoice-processing pipeline used by the UI and CLI.

This is the one place that wires the whole chain together:

    rule engine (M1)
      -> structured explanation (Day 6)
      -> confidence + routing (Day 7)
      -> AI explanation, evidence-only prompt, Gemini or template fallback (Day 8/9)
      -> quality guard: reject unsupported AI claims, fall back safely (Day 10)
      -> audit log every decision, including auto-passes (Day 11)

The deterministic rule engine remains the source of truth throughout: the AI
step can only add/validate an explanation, never change `decision` or `route`.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from src.audit_service import try_save_audit
from src.day6_structured_explanation import create_structured_explanation
from src.day7_routing import add_confidence_and_routing
from src.day9_ai_explainer import generate_ai_explanation
from src.quality_guard import create_quality_checked_result
from src.rule_engine import process_invoices


def process_one_invoice(result: dict[str, Any]) -> dict[str, Any]:
    """Run a single rule-engine result through explanation, AI, and quality guard."""
    structured = create_structured_explanation(result)
    trusted = add_confidence_and_routing(structured)

    if trusted.get("decision") == "passed":
        # Clean rows don't need an AI explanation — nothing to explain.
        trusted["mode"] = "deterministic"
        trusted["quality_checked"] = True
        return trusted

    ai_response = generate_ai_explanation(trusted)
    final_result = create_quality_checked_result(trusted, ai_response)

    # The quality guard only rewrites explanation/evidence text; routing fields
    # always come from the trusted, deterministic result.
    final_result["route"] = trusted.get("route")
    final_result["confidence"] = trusted.get("confidence")
    final_result["uncertainty"] = trusted.get("uncertainty")
    final_result["human_review_required"] = trusted.get("human_review_required", False)
    final_result["review_reason"] = trusted.get("review_reason")
    final_result["rule_details"] = trusted.get("rule_details", [])
    final_result["matched_invoice_ids"] = trusted.get("matched_invoice_ids", [])
    return final_result


def process_invoice_dataframe(
    df: pd.DataFrame,
    filename: str | None = None,
) -> list[dict[str, Any]]:
    """Validate, process, explain, route, and audit-log every invoice."""
    deterministic_results = process_invoices(df)
    final_results = [process_one_invoice(result) for result in deterministic_results]

    for result in final_results:
        audit_status = try_save_audit(result, filename)
        result["audit_logged"] = audit_status.get("success", False)
        if not audit_status.get("success"):
            result["audit_error"] = audit_status.get("error")

    return final_results


def process_invoice_csv(path: str) -> list[dict[str, Any]]:
    """Read and process an invoice CSV through the shared pipeline."""
    from src.paths import resolve_csv

    resolved = resolve_csv(path)
    df = pd.read_csv(resolved)
    return process_invoice_dataframe(df, filename=str(path))
