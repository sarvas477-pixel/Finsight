import pandas as pd

from src.rule_engine import process_invoices


def test_amount_limit():
    df = pd.DataFrame([
        {
            "invoice_id": "TEST001",
            "vendor": "Test Vendor",
            "amount": 20000,
            "category": "IT",
            "invoice_date": "2026-09-10"
        }
    ])

    results = process_invoices(df)

    assert results[0]["status"] == "EXCEPTION"
    assert results[0]["reasons"][0]["rule"] == "AMOUNT_LIMIT"