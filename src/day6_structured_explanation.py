import math
import json
import pandas as pd
def make_json_safe(value):
    if isinstance(value, dict):
        return {
            key: make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    if value is None:
        return None

    if isinstance(value, float) and not math.isfinite(value):
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return value
from src.rule_engine import process_invoices


def create_structured_explanation(result):
    status = result.get("status")
    reasons = make_json_safe(result.get("reasons", []))
    evidence = make_json_safe(result.get("evidence", {}))
   

    if status == "CLEAN":
        return {
            "invoice_id": result.get("invoice_id"),
            "decision": "passed",
            "summary": "Invoice passed all validation checks.",
            "explanation": "No rule violations were found.",
            "evidence_used": evidence,
            "human_review_required": False,
            "rule_ids": []
        }

    messages = [
        reason.get("message", "A rule check failed.")
        for reason in reasons
    ]

    matched_invoice_ids = [
        reason["matched_invoice_id"]
        for reason in reasons
        if reason.get("matched_invoice_id") is not None
    ]

    return {
        "invoice_id": result.get("invoice_id"),
        "decision": "flagged",
        "summary": f"{len(reasons)} issue(s) found.",
        "explanation": " ".join(messages),
        "evidence_used": evidence,
        "rule_details": reasons,
        "matched_invoice_ids": matched_invoice_ids,
        "human_review_required": result.get(
            "human_review_required", True
        ),
        "review_reason": "Rule-engine exception found.",
        "rule_ids": result.get("rule_ids", [])
    }


if __name__ == "__main__":
    df = pd.read_csv("data/invoices.csv")

    rule_results = process_invoices(df)

    for result in rule_results:
        explanation = create_structured_explanation(result)
        print(json.dumps(explanation, indent=2, allow_nan=False))