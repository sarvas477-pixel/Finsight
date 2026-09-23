"""Supabase audit logging for FinSight decisions."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_audit_record(
    result: dict[str, Any],
    filename: str | None = None,
) -> dict[str, Any]:
    """Convert one FinSight result into an audit_events row."""
    return {
        "event_type": "INVOICE_DECISION",
        "invoice_id": result.get("invoice_id"),
        "message": result.get("explanation", "No explanation available."),
        "decision": result.get("decision"),
        "route": result.get("route"),
        "confidence": result.get("confidence"),
        "filename": filename,
        "rule_ids": result.get("rule_ids", []),
        "mode": result.get("mode"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def save_audit_record(
    result: dict[str, Any],
    filename: str | None = None,
) -> dict[str, Any]:
    """Save one invoice decision to Supabase."""
    from src.supabase_client import get_supabase

    record = build_audit_record(result, filename)
    supabase = get_supabase()
    response = supabase.table("audit_events").insert(record).execute()
    return {"success": True, "data": response.data}
