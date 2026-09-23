from __future__ import annotations

from src.audit_logger import save_audit_record


if __name__ == "__main__":
    sample = {
        "invoice_id": "INV001",
        "decision": "flagged",
        "route": "EXCEPTION",
        "confidence": 0.95,
        "explanation": "Test audit event created successfully.",
        "rule_ids": ["AMOUNT_LIMIT"],
        "mode": "test",
    }

    try:
        response = save_audit_record(sample, filename="demo.csv")
        print("Audit event saved successfully!")
        print(response)
    except Exception as error:  # pragma: no cover - external dependency
        print(f"Audit event failed: {error}")
