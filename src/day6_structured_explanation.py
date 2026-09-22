import json
import math

import pandas as pd

from src.rule_engine import process_invoices


def make_json_safe(value):
    """
    Convert pandas/NaN/infinite values into
    JSON-safe Python values.
    """

    if isinstance(value, dict):
        return {
            key: make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            make_json_safe(item)
            for item in value
        ]

    if value is None:
        return None

    if isinstance(value, float):

        if not math.isfinite(value):
            return None

        return value

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return value


def create_structured_explanation(result):
    """
    Convert M1 deterministic result into
    structured explanation data.

    IMPORTANT:
    This function does NOT change the M1 decision.
    """

    status = result.get(
        "status"
    )

    reasons = make_json_safe(
        result.get(
            "reasons",
            []
        )
    )

    evidence = make_json_safe(
        result.get(
            "evidence",
            {}
        )
    )

    rule_ids = result.get(
        "rule_ids",
        []
    )

    # ========================================================
    # CLEAN / AUTO PASS
    # ========================================================

    if status == "CLEAN":

        return {
            "invoice_id": result.get(
                "invoice_id"
            ),

            "decision": "passed",

            "summary": (
                "Invoice passed all "
                "validation checks."
            ),

            "explanation": (
                "No rule violations "
                "were found."
            ),

            "evidence_used": evidence,

            "rule_details": [],

            "matched_invoice_ids": [],

            "rule_ids": [],

            "human_review_required": False,
        }

    # ========================================================
    # EXCEPTION
    # ========================================================

    messages = [
        reason.get(
            "message",
            "A rule check failed."
        )
        for reason in reasons
    ]

    matched_invoice_ids = []

    for reason in reasons:

        ids = reason.get(
            "matched_invoice_ids",
            []
        )

        if ids:
            matched_invoice_ids.extend(
                ids
            )

        elif reason.get(
            "matched_invoice_id"
        ) is not None:

            matched_invoice_ids.append(
                reason[
                    "matched_invoice_id"
                ]
            )

    # Remove duplicates while preserving order

    matched_invoice_ids = list(
        dict.fromkeys(
            matched_invoice_ids
        )
    )

    return {
        "invoice_id": result.get(
            "invoice_id"
        ),

        "decision": "flagged",

        "summary": (
            f"{len(reasons)} issue(s) found."
        ),

        "explanation": " ".join(
            messages
        ),

        "evidence_used": evidence,

        "rule_details": reasons,

        "matched_invoice_ids": (
            matched_invoice_ids
        ),

        "rule_ids": rule_ids,

        "human_review_required": result.get(
            "human_review_required",
            True
        ),

        "review_reason": (
            "Rule-engine exception found."
        ),
    }


if __name__ == "__main__":

    df = pd.read_csv(
        "data/invoices.csv"
    )

    results = process_invoices(
        df
    )

    for result in results:

        explanation = (
            create_structured_explanation(
                result
            )
        )

        print(
            json.dumps(
                explanation,
                indent=2,
                allow_nan=False
            )
        )