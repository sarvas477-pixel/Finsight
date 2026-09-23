"""Day 13 — reports and usability.

Pure helpers for the dashboard's summary stats, search/filter, and CSV
export. Kept separate from app.py (which needs Streamlit) so they can be
unit tested directly.
"""
from __future__ import annotations

from typing import Any

ROUTES = ("AUTO_PASS", "EXCEPTION", "HUMAN_REVIEW")


def build_summary(results: list[dict[str, Any]]) -> dict[str, int]:
    """Totals and per-queue counts for the metrics row."""
    return {
        "total": len(results),
        "auto_pass": sum(1 for r in results if r.get("route") == "AUTO_PASS"),
        "exceptions": sum(1 for r in results if r.get("route") == "EXCEPTION"),
        "human_review": sum(1 for r in results if r.get("route") == "HUMAN_REVIEW"),
        "audit_logged": sum(1 for r in results if r.get("audit_logged")),
    }


def filter_results(
    results: list[dict[str, Any]],
    query: str | None = None,
    route: str | None = None,
) -> list[dict[str, Any]]:
    """Filter by route and/or a free-text search across id, vendor-ish text,
    explanation, and rule ids."""
    filtered = results

    if route and route != "ALL":
        filtered = [r for r in filtered if r.get("route") == route]

    if query:
        needle = query.strip().lower()
        if needle:
            filtered = [
                r
                for r in filtered
                if needle in str(r.get("invoice_id", "")).lower()
                or needle in str(r.get("explanation", "")).lower()
                or any(needle in str(rid).lower() for rid in r.get("rule_ids", []))
            ]

    return filtered


def to_report_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten pipeline results into the table/CSV-export shape."""
    rows = []
    for item in results:
        rows.append(
            {
                "Invoice ID": item.get("invoice_id"),
                "Queue": item.get("route", "UNKNOWN"),
                "Confidence": f"{item.get('confidence', 0):.0%}",
                "Mode": item.get("mode", "—"),
                "Rules": ", ".join(item.get("rule_ids", [])) or "—",
                "Explanation": item.get("explanation", ""),
                "Audit Logged": "Yes" if item.get("audit_logged") else "No",
            }
        )
    return rows
