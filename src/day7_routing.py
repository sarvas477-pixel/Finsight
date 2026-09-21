import json
import pandas as pd

from src.rule_engine import process_invoices
from src.day6_structured_explanation import (
    create_structured_explanation,
)


UNCERTAIN_RULES = {
    "DUPLICATE_INVOICE",
    "DUPLICATE_INVOICE_ID",
}


def add_confidence_and_routing(explanation):
    rule_ids = set(explanation.get("rule_ids", []))

    # Clean invoice: automatically pass it.
    if explanation.get("decision") == "passed":
        explanation["confidence"] = 1.0
        explanation["uncertainty"] = "low"
        explanation["route"] = "AUTO_PASS"
        explanation["human_review_required"] = False
        return explanation

    # A possible duplicate needs a human to confirm it.
    if rule_ids.intersection(UNCERTAIN_RULES):
        explanation["confidence"] = 0.60
        explanation["uncertainty"] = "high"
        explanation["route"] = "HUMAN_REVIEW"
        explanation["human_review_required"] = True
        explanation["review_reason"] = (
            "Possible duplicate requires human confirmation."
        )
        return explanation

    # Clear rule violations are high-confidence exceptions.
    explanation["confidence"] = 0.95
    explanation["uncertainty"] = "low"

    if explanation.get("human_review_required"):
        explanation["route"] = "HUMAN_REVIEW"
    else:
        explanation["route"] = "EXCEPTION"

    return explanation


if __name__ == "__main__":
    df = pd.read_csv("data/invoices.csv")

    rule_results = process_invoices(df)

    for result in rule_results:
        explanation = create_structured_explanation(result)
        routed_explanation = add_confidence_and_routing(explanation)

        print(json.dumps(
            routed_explanation,
            indent=2,
            allow_nan=False
        ))