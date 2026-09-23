"""Safe audit service wrapper."""
from __future__ import annotations

from typing import Any

from src.audit_logger import save_audit_record


def try_save_audit(
    result: dict[str, Any],
    filename: str | None = None,
) -> dict[str, Any]:
    """Attempt to record a decision but never let Supabase failures kill the run."""
    try:
        return save_audit_record(result, filename)
    except Exception as error:  # pragma: no cover - external dependency
        return {"success": False, "error": str(error)}
