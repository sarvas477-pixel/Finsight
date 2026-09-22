import pandas as pd

from src.invoice_pipeline import process_invoice_dataframe


def test_deterministic_exception_is_not_hidden_in_human_review():
    results = process_invoice_dataframe(pd.DataFrame([
        {
            "invoice_id": "INV-1",
            "vendor": "Vendor",
            "amount": -10,
            "category": "IT",
            "invoice_date": "2026-09-22",
        }
    ]))

    assert results[0]["status"] == "flagged" if "status" in results[0] else True
    assert results[0]["route"] == "EXCEPTION"
    assert "INVALID_AMOUNT" in results[0]["rule_ids"]
