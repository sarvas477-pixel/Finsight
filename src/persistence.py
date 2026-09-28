import os
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

def save_audit_event(event_type, invoice_id, message):
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key:
        return False, "Supabase is not configured."
    try:
        from supabase import create_client
        client = create_client(url, key)
        client.table("audit_events").insert({
            "event_type": event_type,
            "invoice_id": str(invoice_id),
            "message": message,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        return True, "Saved."
    except Exception as exc:
        return False, str(exc)

def save_review_action(invoice_id, action, comment):
    return save_audit_event("REVIEW_ACTION", invoice_id, f"{action}: {comment}".strip())
