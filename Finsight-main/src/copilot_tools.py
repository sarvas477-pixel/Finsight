"""Tool layer for FinSight Copilot.

The Copilot never queries the database or mutates invoice state directly from an
LLM prompt. These small, deterministic tools operate on trusted analysis data
and return structured evidence that can be grounded in an AI response.
"""
from __future__ import annotations

from typing import Any


def _normalise(value: Any) -> str:
    return str(value or "").strip().casefold()


def get_invoice(invoice_id: str, results: list[dict[str, Any]] | None) -> dict[str, Any]:
    target = _normalise(invoice_id)
    for result in results or []:
        if _normalise(result.get("invoice_id")) == target:
            return {"ok": True, "invoice": result}
    return {"ok": False, "error": f"Invoice {invoice_id} was not found in the analyzed dataset."}


def search_invoices(
    query: str = "",
    results: list[dict[str, Any]] | None = None,
    status: str | None = None,
    vendor: str | None = None,
) -> dict[str, Any]:
    q = _normalise(query)
    wanted_status = _normalise(status)
    wanted_vendor = _normalise(vendor)
    matches = []
    for result in results or []:
        evidence = result.get("evidence") or {}
        haystack = " ".join(
            _normalise(evidence.get(key))
            for key in ("invoice_id", "vendor", "category", "invoice_date")
        )
        if q and q not in haystack:
            continue
        if wanted_status and _normalise(result.get("status")) != wanted_status:
            continue
        if wanted_vendor and wanted_vendor not in _normalise(evidence.get("vendor")):
            continue
        matches.append(result)
    return {"ok": True, "count": len(matches), "invoices": matches}


def get_exceptions(results: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    exceptions = [r for r in results or [] if r.get("status") == "EXCEPTION"]
    return {"ok": True, "count": len(exceptions), "exceptions": exceptions}


def get_review_queue(results: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    queue = [r for r in results or [] if r.get("human_review_required")]
    return {"ok": True, "count": len(queue), "invoices": queue}


def find_potential_duplicates(
    invoice_id: str,
    results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    invoice = get_invoice(invoice_id, results)
    if not invoice["ok"]:
        return invoice
    result = invoice["invoice"]
    duplicate_reasons = [
        reason for reason in result.get("reasons", [])
        if reason.get("rule") in {"DUPLICATE_INVOICE", "DUPLICATE_INVOICE_ID"}
    ]
    return {
        "ok": True,
        "invoice_id": invoice_id,
        "potential_duplicates": duplicate_reasons,
        "count": len(duplicate_reasons),
    }


def explain_invoice(invoice_id: str, results: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    invoice = get_invoice(invoice_id, results)
    if not invoice["ok"]:
        return invoice
    result = invoice["invoice"]
    evidence = result.get("evidence") or {}
    return {
        "ok": True,
        "invoice_id": result.get("invoice_id"),
        "status": result.get("status"),
        "route": result.get("route"),
        "confidence": result.get("confidence"),
        "findings": result.get("reasons", []),
        "evidence": evidence,
        "recommendation": (
            "Review the flagged evidence before making a final decision."
            if result.get("human_review_required")
            else "No human review is currently required."
        ),
    }


def get_statistics(results: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = results or []
    total = len(rows)
    clean = sum(r.get("status") == "CLEAN" for r in rows)
    exceptions = sum(r.get("status") == "EXCEPTION" for r in rows)
    review = sum(bool(r.get("human_review_required")) for r in rows)
    return {
        "ok": True,
        "total": total,
        "clean": clean,
        "exceptions": exceptions,
        "human_review": review,
        "potential_duplicates": sum(
            any(
                reason.get("rule") == "DUPLICATE_INVOICE"
                for reason in r.get("reasons", [])
            )
            for r in rows
        ),
    }


def build_tool_context(
    question: str,
    results: list[dict[str, Any]] | None,
    current_invoice_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve a compact evidence package for an AI response."""
    context: dict[str, Any] = {
        "question": question,
        "current_invoice_id": current_invoice_id,
        "statistics": get_statistics(results),
    }

    target = current_invoice_id
    if not target:
        import re
        match = re.search(r"\b(?:inv|invoice)[-_ ]?([a-z0-9]{2,})\b", question, re.I)
        if match:
            target = match.group(0)

    if target:
        context["invoice"] = explain_invoice(target, results)
        context["duplicates"] = find_potential_duplicates(target, results)

    q = _normalise(question)
    if any(term in q for term in ("review", "attention", "need my attention")):
        context["review_queue"] = get_review_queue(results)
    if any(term in q for term in ("exception", "flagged", "problem")):
        context["exceptions"] = get_exceptions(results)
    if any(term in q for term in ("duplicate", "similar")) and target:
        context["duplicates"] = find_potential_duplicates(target, results)

    return context
