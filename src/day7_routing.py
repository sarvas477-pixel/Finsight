import json

import pandas as pd

from src.rule_engine import process_invoices
from src.day6_structured_explanation import create_structured_explanation


# These rules are ambiguous or incomplete-data cases and should be reviewed by a person.
# Deterministic violations (for example invalid amounts and configured limits) remain
# visible in the EXCEPTION queue.
UNCERTAIN_RULES = {
    "DUPLICATE_INVOICE",
    "DUPLICATE_INVOICE_ID",
    "MISSING_REQUIRED_FIELD",
    "INVALID_DATE",
}


def add_confidence_and_routing(explanation):
    """Attach a user-facing queue without hiding deterministic exceptions.

    ``human_review_required`` describes the rule result; it must not be used to
    classify every exception as HUMAN_REVIEW. Previously every rule set that
    field to True, which made the EXCEPTION queue permanently empty.
    """
    rule_ids = set(explanation.get("rule_ids", []))

    if explanation.get("decision") == "passed":
        explanation.update(
            confidence=1.0,
            uncertainty="low",
            route="AUTO_PASS",
            human_review_required=False,
        )
        return explanation

    if rule_ids.intersection(UNCERTAIN_RULES):
        explanation.update(
            confidence=0.60,
            uncertainty="high",
            route="HUMAN_REVIEW",
            human_review_required=True,
            review_reason="Incomplete or ambiguous invoice data requires human confirmation.",
        )
        return explanation

    # Clear, deterministic rule violations belong in the exception queue even
    # though the record may still require operational follow-up.
    explanation.update(
        confidence=0.95,
        uncertainty="low",
        route="EXCEPTION",
    )
    return explanation


if __name__ == "__main__":
    df = pd.read_csv("data/invoices.csv")
    for result in process_invoices(df):
        print(json.dumps(add_confidence_and_routing(create_structured_explanation(result)), indent=2, allow_nan=False))
