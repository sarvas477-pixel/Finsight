import pandas as pd
import pytest

from src.rule_engine import (
    process_invoices,
    summarize_results,
)


# ============================================================
# TEST DATA HELPER
# ============================================================

def invoice(**overrides):
    """
    Create a valid test invoice.

    Individual tests can override any field.
    """

    row = {
        "invoice_id": "TEST001",
        "vendor": "Test Vendor",
        "amount": 5000,
        "category": "IT",
        "invoice_date": "2026-09-10",
    }

    row.update(overrides)

    return row


# ============================================================
# RULE HELPER
# ============================================================

def rules(result):
    """
    Return all rule IDs triggered by an invoice.
    """

    return [
        reason["rule"]
        for reason in result.get(
            "reasons",
            []
        )
    ]


# ============================================================
# BASIC VALIDATION TESTS
# ============================================================

def test_clean_invoice():

    results = process_invoices(
        pd.DataFrame([
            invoice()
        ])
    )

    assert len(results) == 1

    assert results[0]["status"] == "CLEAN"

    assert results[0][
        "human_review_required"
    ] is False

    assert results[0]["rule_ids"] == []

    assert results[0]["reasons"] == []


def test_missing_vendor():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                vendor=""
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "MISSING_REQUIRED_FIELD"
        in rules(results[0])
    )

    assert results[0][
        "human_review_required"
    ] is True


def test_missing_invoice_id():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                invoice_id=""
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "MISSING_REQUIRED_FIELD"
        in rules(results[0])
    )


def test_missing_amount():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                amount=None
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "MISSING_REQUIRED_FIELD"
        in rules(results[0])
    )


def test_missing_category():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                category=""
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "MISSING_REQUIRED_FIELD"
        in rules(results[0])
    )


def test_missing_invoice_date():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                invoice_date=""
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "MISSING_REQUIRED_FIELD"
        in rules(results[0])
    )


# ============================================================
# AMOUNT TESTS
# ============================================================

def test_amount_limit():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                amount=15001,
                category="Travel"
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "AMOUNT_LIMIT"
        in rules(results[0])
    )


def test_amount_at_limit_is_clean():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                amount=15000,
                category="Travel"
            )
        ])
    )

    assert results[0]["status"] == "CLEAN"


def test_negative_amount():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                amount=-100
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "INVALID_AMOUNT"
        in rules(results[0])
    )


def test_zero_amount():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                amount=0
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "INVALID_AMOUNT"
        in rules(results[0])
    )


def test_text_amount():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                amount="abc"
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "INVALID_AMOUNT"
        in rules(results[0])
    )


def test_infinite_amount():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                amount=float("inf")
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "INVALID_AMOUNT"
        in rules(results[0])
    )


def test_negative_infinite_amount():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                amount=float("-inf")
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "INVALID_AMOUNT"
        in rules(results[0])
    )


# ============================================================
# FIELD VALIDATION TESTS
# ============================================================

def test_blank_invoice_id():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                invoice_id=""
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "MISSING_REQUIRED_FIELD"
        in rules(results[0])
    )


def test_whitespace_vendor():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                vendor="   "
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "MISSING_REQUIRED_FIELD"
        in rules(results[0])
    )


def test_invalid_date():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                invoice_date="not-a-date"
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "INVALID_DATE"
        in rules(results[0])
    )


def test_unknown_category():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                category="RandomCategory"
            )
        ])
    )

    assert results[0]["status"] == "EXCEPTION"

    assert (
        "UNKNOWN_CATEGORY"
        in rules(results[0])
    )


# ============================================================
# DUPLICATE TESTS
# ============================================================

def test_duplicate_invoice_id():

    results = process_invoices(
        pd.DataFrame([

            invoice(
                invoice_id="INV001"
            ),

            invoice(
                invoice_id="INV001"
            ),

        ])
    )

    assert results[0]["status"] == "CLEAN"

    assert results[1]["status"] == "EXCEPTION"

    assert (
        "DUPLICATE_INVOICE_ID"
        in rules(results[1])
    )


def test_content_duplicate():

    results = process_invoices(
        pd.DataFrame([

            invoice(
                invoice_id="INV001",
                vendor="ABC",
                amount=4500,
                category="Travel",
                invoice_date="2026-09-14",
            ),

            invoice(
                invoice_id="INV002",
                vendor="ABC",
                amount=4500,
                category="Travel",
                invoice_date="2026-09-14",
            ),

        ])
    )

    assert results[0]["status"] == "CLEAN"

    assert results[1]["status"] == "EXCEPTION"

    assert (
        "DUPLICATE_INVOICE"
        in rules(results[1])
    )


def test_duplicate_evidence_contains_ids():

    results = process_invoices(
        pd.DataFrame([

            invoice(
                invoice_id="INV001",
                vendor="ABC",
                amount=4500,
                category="Travel",
                invoice_date="2026-09-14",
            ),

            invoice(
                invoice_id="INV002",
                vendor="ABC",
                amount=4500,
                category="Travel",
                invoice_date="2026-09-14",
            ),

        ])
    )

    duplicate = next(
        reason
        for reason in results[1]["reasons"]
        if reason["rule"]
        == "DUPLICATE_INVOICE"
    )

    assert (
        duplicate["matched_invoice_id"]
        == "INV001"
    )

    assert (
        duplicate["matched_invoice_ids"]
        == ["INV001"]
    )


def test_different_vendor_not_duplicate():

    results = process_invoices(
        pd.DataFrame([

            invoice(
                invoice_id="INV001",
                vendor="ABC",
                amount=4500,
                invoice_date="2026-09-14",
            ),

            invoice(
                invoice_id="INV002",
                vendor="XYZ",
                amount=4500,
                invoice_date="2026-09-14",
            ),

        ])
    )

    assert results[1]["status"] == "CLEAN"


def test_different_amount_not_duplicate():

    results = process_invoices(
        pd.DataFrame([

            invoice(
                invoice_id="INV001",
                vendor="ABC",
                amount=4500,
                invoice_date="2026-09-14",
            ),

            invoice(
                invoice_id="INV002",
                vendor="ABC",
                amount=5000,
                invoice_date="2026-09-14",
            ),

        ])
    )

    assert results[1]["status"] == "CLEAN"


def test_different_date_not_duplicate():

    results = process_invoices(
        pd.DataFrame([

            invoice(
                invoice_id="INV001",
                vendor="ABC",
                amount=4500,
                invoice_date="2026-09-14",
            ),

            invoice(
                invoice_id="INV002",
                vendor="ABC",
                amount=4500,
                invoice_date="2026-09-15",
            ),

        ])
    )

    assert results[1]["status"] == "CLEAN"


# ============================================================
# DATAFRAME VALIDATION
# ============================================================

def test_missing_required_column():

    df = pd.DataFrame([
        {
            "invoice_id": "INV001",
            "vendor": "ABC",
            "amount": 1000,
            "category": "IT",
            # invoice_date intentionally missing
        }
    ])

    with pytest.raises(
        ValueError,
        match="Missing required CSV columns",
    ):

        process_invoices(df)


def test_duplicate_columns():

    df = pd.DataFrame(
        [
            [
                "INV001",
                "Vendor",
                1000,
                "IT",
                "IT_DUPLICATE",
                "2026-09-10",
            ]
        ],
        columns=[
            "invoice_id",
            "vendor",
            "amount",
            "category",
            "amount",
            "invoice_date",
        ],
    )

    with pytest.raises(
        ValueError,
        match="Duplicate CSV columns",
    ):
        process_invoices(df)

# ============================================================
# MULTIPLE RULES
# ============================================================

def test_multiple_exceptions_same_invoice():

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

    result = results[0]

    assert result["status"] == "EXCEPTION"

    assert (
        "MISSING_REQUIRED_FIELD"
        in rules(result)
    )

    assert (
        "INVALID_AMOUNT"
        in rules(result)
    )

    assert (
        "INVALID_DATE"
        in rules(result)
    )

    assert (
        "UNKNOWN_CATEGORY"
        in rules(result)
    )

    assert len(
        result["rule_ids"]
    ) >= 4


# ============================================================
# SUMMARY TESTS
# ============================================================

def test_summary():

    results = process_invoices(
        pd.DataFrame([

            invoice(
                invoice_id="INV001"
            ),

            invoice(
                invoice_id="INV002",
                amount=20000,
                category="Travel"
            ),

            invoice(
                invoice_id="INV003",
                vendor=""
            ),

        ])
    )

    summary = summarize_results(
        results
    )

    assert summary["total"] == 3

    assert summary["clean"] == 1

    assert summary["exceptions"] == 2

    assert (
        summary["review_required"]
        == 2
    )


# ============================================================
# EVIDENCE TESTS
# ============================================================

def test_evidence_exists_for_clean_invoice():

    results = process_invoices(
        pd.DataFrame([
            invoice()
        ])
    )

    evidence = results[0][
        "evidence"
    ]

    assert (
        evidence["invoice_id"]
        == "TEST001"
    )

    assert (
        evidence["vendor"]
        == "Test Vendor"
    )

    assert (
        evidence["amount"]
        == 5000
    )

    assert (
        evidence["category"]
        == "IT"
    )


def test_evidence_for_amount_limit():

    results = process_invoices(
        pd.DataFrame([
            invoice(
                amount=20000,
                category="Travel"
            )
        ])
    )

    reason = next(
        reason
        for reason in results[0]["reasons"]
        if reason["rule"]
        == "AMOUNT_LIMIT"
    )

    assert (
        reason["actual_value"]
        == 20000
    )

    assert (
        reason["expected_value"]
        == 15000
    )


# ============================================================
# AI INPUT CONTRACT
# ============================================================

def test_ai_input_contract():

    from src.m1_ai_input import (
        prepare_ai_input
    )

    result = process_invoices(
        pd.DataFrame([
            invoice()
        ])
    )[0]

    ai_input = prepare_ai_input(
        result
    )

    assert (
        ai_input["invoice_id"]
        == "TEST001"
    )

    assert (
        ai_input["status"]
        == "CLEAN"
    )

    assert (
        ai_input[
            "human_review_required"
        ] is False
    )

    assert "rule_ids" in ai_input

    assert "reasons" in ai_input

    assert "evidence" in ai_input


def test_ai_input_exception_contract():

    from src.m1_ai_input import (
        prepare_ai_input
    )

    result = process_invoices(
        pd.DataFrame([
            invoice(
                amount=20000,
                category="Travel"
            )
        ])
    )[0]

    ai_input = prepare_ai_input(
        result
    )

    assert (
        ai_input["status"]
        == "EXCEPTION"
    )

    assert (
        ai_input[
            "human_review_required"
        ] is True
    )

    assert (
        "AMOUNT_LIMIT"
        in ai_input["rule_ids"]
    )


# ============================================================
# BATCH AI INPUT
# ============================================================

def test_batch_ai_input():

    from src.m1_ai_input import (
        prepare_batch_ai_input
    )

    results = process_invoices(
        pd.DataFrame([

            invoice(
                invoice_id="INV001"
            ),

            invoice(
                invoice_id="INV002",
                amount=20000,
                category="Travel"
            ),

        ])
    )

    ai_inputs = prepare_batch_ai_input(
        results
    )

    assert len(ai_inputs) == 2

    assert (
        ai_inputs[0]["invoice_id"]
        == "INV001"
    )

    assert (
        ai_inputs[1]["invoice_id"]
        == "INV002"
    )

    assert (
        ai_inputs[0]["status"]
        == "CLEAN"
    )

    assert (
        ai_inputs[1]["status"]
        == "EXCEPTION"
    )