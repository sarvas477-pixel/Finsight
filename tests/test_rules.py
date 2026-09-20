import pandas as pd
import pytest

from src.rule_engine import (
    process_invoices,
    summarize_results,
)


def invoice(**overrides):

    row = {
        "invoice_id": "TEST001",
        "vendor": "Test Vendor",
        "amount": 5000,
        "category": "IT",
        "invoice_date": "2026-09-10",
    }

    row.update(overrides)

    return row


def rules(result):

    return [
        reason["rule"]
        for reason in result["reasons"]
    ]


def test_clean_invoice():

    results = process_invoices(
        pd.DataFrame([
            invoice()
        ])
    )

    assert results[0]["status"] == "CLEAN"
    assert results[0]["human_review_required"] is False
    assert results[0]["rule_ids"] == []


def test_amount_limit():

    results = process_invoices(
        pd.DataFrame([
            invoice(amount=20000)
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert "AMOUNT_LIMIT" in rules(
        results[0]
    )

    assert results[0]["human_review_required"] is True


def test_missing_vendor():

    results = process_invoices(
        pd.DataFrame([
            invoice(vendor="")
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "MISSING_REQUIRED_FIELD"
        in rules(results[0])
    )


def test_duplicate_invoice_id():

    results = process_invoices(
        pd.DataFrame([
            invoice(invoice_id="DUP001"),
            invoice(
                invoice_id="DUP001",
                amount=7000
            ),
        ])
    )

    assert results[1]["status"] == "EXCEPTION"

    duplicate = next(
        r
        for r in results[1]["reasons"]
        if r["rule"] == "DUPLICATE_INVOICE_ID"
    )

    assert duplicate["matched_invoice_id"] == "DUP001"


def test_content_duplicate():

    results = process_invoices(
        pd.DataFrame([

            invoice(
                invoice_id="INV001",
                vendor="ABC Suppliers",
                amount=4500,
                category="Travel",
                invoice_date="2026-09-14",
            ),

            invoice(
                invoice_id="INV003",
                vendor="ABC Suppliers",
                amount=4500,
                category="Travel",
                invoice_date="2026-09-14",
            ),

        ])
    )

    assert results[0]["status"] == "CLEAN"

    assert results[1]["status"] == "EXCEPTION"

    duplicate = next(
        r
        for r in results[1]["reasons"]
        if r["rule"] == "DUPLICATE_INVOICE"
    )

    assert duplicate["matched_invoice_id"] == "INV001"


def test_unknown_category():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                category="SomethingElse",
                amount=100,
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "UNKNOWN_CATEGORY"
        in rules(results[0])
    )


def test_missing_required_columns():

    df = pd.DataFrame([
        {
            "invoice_id": "X",
            "vendor": "Vendor",
        }
    ])

    with pytest.raises(
        ValueError,
        match="Missing required CSV columns",
    ):

        process_invoices(df)


def test_invalid_amount_negative():

    results = process_invoices(
        pd.DataFrame([
            invoice(amount=-1)
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "INVALID_AMOUNT"
        in rules(results[0])
    )


def test_invalid_amount_text():

    results = process_invoices(
        pd.DataFrame([
            invoice(amount="abc")
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "INVALID_AMOUNT"
        in rules(results[0])
    )


def test_invalid_date():

    results = process_invoices(
        pd.DataFrame([
            invoice(invoice_date="not-a-date")
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "INVALID_DATE"
        in rules(results[0])
    )


def test_case_insensitive_category():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                category="it",
                amount=5000,
            )
        ])
    )

    assert results[0]["status"] == "CLEAN"


def test_multiple_exceptions():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                vendor="",
                amount=-500,
                category="Unknown",
                invoice_date="bad-date",
            )
        ])
    )

    result_rules = rules(results[0])

    assert "MISSING_REQUIRED_FIELD" in result_rules
    assert "INVALID_AMOUNT" in result_rules
    assert "UNKNOWN_CATEGORY" in result_rules
    assert "INVALID_DATE" in result_rules


def test_summary():

    results = process_invoices(
        pd.DataFrame([
            invoice(invoice_id="A"),
            invoice(invoice_id="B", amount=20000),
            invoice(invoice_id="C", vendor=""),
        ])
    )

    summary = summarize_results(results)

    assert summary["total"] == 3
    assert summary["clean"] == 1
    assert summary["exceptions"] == 2
    assert summary["review_required"] == 2