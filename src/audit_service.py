"""Safe wrappers around Supabase calls.

Every function here catches infrastructure failures (no credentials, no
network, table doesn't exist yet) and returns a status dict instead of
raising, so the dashboard and CLI keep working in demo mode with no
Supabase project set up. Bad *input* (an invalid review action, an empty
comment) is a real usage error and is left to raise, so the caller can show
it to the person instead of silently swallowing it.
"""
from __future__ import annotations

from typing import Any

from src.audit_logger import save_audit_record
from src.save_review import save_review_action


def try_save_audit(
    result: dict[str, Any],
    filename: str | None = None,
) -> dict[str, Any]:
    """Attempt to record a decision but never let Supabase failures kill the run."""
    try:
        return save_audit_record(result, filename)
    except Exception as error:  # pragma: no cover - external dependency
        return {"success": False, "error": str(error)}


def validate_review_action(action: str, comment: str) -> None:
    """Same validation save_review_action does, run up front so the UI can
    show a clean inline error before ever touching Supabase."""
    if action not in {"APPROVED", "REJECTED"}:
        raise ValueError("Action must be APPROVED or REJECTED.")
    if not comment.strip():
        raise ValueError("Reviewer comment cannot be empty.")


def try_save_review(
    invoice_id: str,
    action: str,
    comment: str,
    reviewer_id: str = "demo_reviewer",
) -> dict[str, Any]:
    """Attempt to record a human review action.

    Raises ValueError for bad input (invalid action, empty comment) so the UI
    can show that inline. Any Supabase/infra failure is caught and reported
    as a soft failure instead.
    """
    validate_review_action(action, comment)
    try:
        response = save_review_action(invoice_id, action, comment, reviewer_id)
        return {"success": True, "data": getattr(response, "data", None)}
    except Exception as error:  # pragma: no cover - external dependency
        return {"success": False, "error": str(error)}


def try_fetch_audit_events(limit: int = 50) -> dict[str, Any]:
    """Attempt to fetch recent audit_events rows for the audit-log viewer."""
    try:
        from src.supabase_client import get_supabase

        supabase = get_supabase()
        response = (
            supabase.table("audit_events")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {"success": True, "data": response.data}
    except Exception as error:  # pragma: no cover - external dependency
        return {"success": False, "error": str(error), "data": []}