"""Store human review actions in Supabase."""
from __future__ import annotations

from datetime import datetime, timezone


def save_review_action(
    invoice_id: str,
    action: str,
    comment: str,
    reviewer_id: str = "demo_reviewer",
):
    """Persist a review decision to the review_actions table if the schema exists."""
    if action not in {"APPROVED", "REJECTED"}:
        raise ValueError("Action must be APPROVED or REJECTED.")
    if not comment.strip():
        raise ValueError("Reviewer comment cannot be empty.")

    from src.supabase_client import get_supabase

    record = {
        "invoice_id": invoice_id,
        "reviewer_id": reviewer_id,
        "action": action,
        "comment": comment.strip(),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    return get_supabase().table("review_actions").insert(record).execute()
