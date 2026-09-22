import pandas as pd

from src.invoice_pipeline import process_invoice_dataframe


def test_fake_csv_covers_main_routes():
    df = pd.read_csv("tests/fixtures/fake_invoices.csv")
    results = process_invoice_dataframe(df)

    assert len(results) == 5
    assert [result["route"] for result in results] == [
        "AUTO_PASS",
        "HUMAN_REVIEW",
        "EXCEPTION",
        "EXCEPTION",
        "HUMAN_REVIEW",
    ]
    assert sum(result["route"] == "EXCEPTION" for result in results) == 2
    assert "MISSING_REQUIRED_FIELD" in results[1]["rule_ids"]
    assert "INVALID_AMOUNT" in results[2]["rule_ids"]
    assert "AMOUNT_LIMIT" in results[3]["rule_ids"]
    assert "DUPLICATE_INVOICE" in results[4]["rule_ids"]
