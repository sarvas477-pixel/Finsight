import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()


def _secret(name):
    value = os.getenv(name)
    if value:
        return str(value)
    try:
        import streamlit as st
        value = st.secrets.get(name)
        return str(value) if value else None
    except Exception:
        return None


def _client():
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_KEY")
    if not url or not key:
        return None
    from supabase import create_client
    return create_client(url, key)


def _schema_issue(exc):
    """Return a human-friendly message for schema-related Supabase failures."""
    text = str(exc).lower()
    if "column" in text and "does not exist" in text:
        return "Supabase schema mismatch: run SUPABASE_FIX.sql in your Supabase SQL editor."
    if "42703" in text:
        return "Supabase schema mismatch: missing column in audit_events. Run SUPABASE_FIX.sql."
    return None


def test_supabase_connection():
    try:
        client = _client()
        if client is None:
            return False, "SUPABASE_URL / SUPABASE_KEY are not configured."
        client.table("audit_events").select("*").limit(1).execute()
        return True, "Supabase audit_events is reachable."
    except Exception as exc:
        msg = _schema_issue(exc)
        if msg:
            return False, msg
        return False, f"{type(exc).__name__}: {exc}"


def save_audit_event(event_type, invoice_id, message, metadata=None):
    try:
        client = _client()
        if client is None:
            return False, "Supabase is not configured."
        payload = {
            "event_type": event_type,
            "invoice_id": str(invoice_id),
            "message": message,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if metadata is not None:
            payload["metadata"] = metadata
        client.table("audit_events").insert(payload).execute()
        return True, "Saved."
    except Exception as exc:
        msg = _schema_issue(exc)
        if msg:
            return False, msg
        return False, str(exc)


def save_review_action(invoice_id, action, comment):
    return save_audit_event("REVIEW_ACTION", invoice_id, f"{action}: {comment}".strip())


def save_decision(result):
    return save_audit_event(
        "DECISION",
        result["invoice_id"],
        f"{result['status']} / {result.get('route')}",
        {"rule_ids": result["rule_ids"], "confidence": result.get("confidence")},
    )


def save_audit_events(events):
    """Insert many audit events in ONE request (instead of one call per row).

    events: iterable of dicts with event_type, invoice_id, message, metadata(optional).
    Best-effort: returns (ok, message) and never raises.
    """
    events = list(events)
    if not events:
        return True, "Nothing to save."
    try:
        client = _client()
        if client is None:
            return False, "Supabase is not configured."
        now = datetime.now(timezone.utc).isoformat()
        rows = []
        for e in events:
            row = {
                "event_type": e["event_type"],
                "invoice_id": str(e.get("invoice_id", "")),
                "message": e["message"],
                "created_at": now,
            }
            if e.get("metadata") is not None:
                row["metadata"] = e["metadata"]
            rows.append(row)
        for start in range(0, len(rows), 500):
            client.table("audit_events").insert(rows[start:start + 500]).execute()
        return True, f"Saved {len(rows)} events."
    except Exception as exc:
        msg = _schema_issue(exc)
        if msg:
            return False, msg
        return False, str(exc)


def fetch_audit_events(limit=200):
    """Return (ok, rows_or_message): newest persisted audit events first."""
    try:
        client = _client()
        if client is None:
            return False, "SUPABASE_URL / SUPABASE_KEY are not configured."
        resp = (
            client.table("audit_events")
            .select("created_at,event_type,invoice_id,message,metadata")
            .order("created_at", desc=True)
            .limit(int(limit))
            .execute()
        )
        return True, resp.data or []
    except Exception as exc:
        msg = _schema_issue(exc)
        if msg:
            return False, msg
        return False, f"{type(exc).__name__}: {exc}"
