import os
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

def _secret(name):
    value = os.getenv(name)
    if value: return str(value)
    try:
        import streamlit as st
        value = st.secrets.get(name)
        return str(value) if value else None
    except Exception: return None

def _client():
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_KEY")
    if not url or not key: return None
    from supabase import create_client
    return create_client(url, key)

def test_supabase_connection():
    try:
        client = _client()
        if client is None: return False, "SUPABASE_URL / SUPABASE_KEY are not configured."
        client.table("audit_events").select("*").limit(1).execute()
        return True, "Supabase audit_events is reachable."
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"

def save_audit_event(event_type, invoice_id, message, metadata=None):
    try:
        client = _client()
        if client is None: return False, "Supabase is not configured."
        payload = {"event_type": event_type, "invoice_id": str(invoice_id), "message": message,
                   "created_at": datetime.now(timezone.utc).isoformat()}
        if metadata is not None: payload["metadata"] = metadata
        client.table("audit_events").insert(payload).execute()
        return True, "Saved."
    except Exception as exc: return False, str(exc)

def save_review_action(invoice_id, action, comment):
    return save_audit_event("REVIEW_ACTION", invoice_id, f"{action}: {comment}".strip())

def save_decision(result):
    return save_audit_event("DECISION", result["invoice_id"],
                            f"{result['status']} / {result.get('route')}",
                            {"rule_ids": result["rule_ids"], "confidence": result.get("confidence")})

def save_audit_events(events):
    events = list(events)
    if not events: return True, "Nothing to save."
    try:
        client = _client()
        if client is None: return False, "Supabase is not configured."
        now = datetime.now(timezone.utc).isoformat()
        rows = []
        for event in events:
            row = {"event_type": event["event_type"], "invoice_id": str(event.get("invoice_id", "")),
                   "message": event["message"], "created_at": now}
            if event.get("metadata") is not None: row["metadata"] = event["metadata"]
            rows.append(row)
        for start in range(0, len(rows), 500):
            client.table("audit_events").insert(rows[start:start + 500]).execute()
        return True, f"Saved {len(rows)} events."
    except Exception as exc: return False, str(exc)

def fetch_audit_events(limit=200):
    try:
        client = _client()
        if client is None: return False, "SUPABASE_URL / SUPABASE_KEY are not configured."
        response = (client.table("audit_events")
                    .select("created_at,event_type,invoice_id,message,metadata")
                    .order("created_at", desc=True).limit(int(limit)).execute())
        return True, response.data or []
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
