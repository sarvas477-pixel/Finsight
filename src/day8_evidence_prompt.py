import json
import pandas as pd

from src.rule_engine import process_invoices
from src.day6_structured_explanation import (
    create_structured_explanation,
)
from src.day7_routing import add_confidence_and_routing


def create_evidence_only_prompt(explanation):
    trusted_data = {
        "invoice_id": explanation.get("invoice_id"),
        "decision": explanation.get("decision"),
        "rule_ids": explanation.get("rule_ids", []),
        "rule_details": explanation.get("rule_details", []),
        "evidence_used": explanation.get("evidence_used", {}),
        "matched_invoice_ids": explanation.get(
            "matched_invoice_ids", []
        ),
    }

    return f"""
You are a FinSight Accounts Payable audit assistant.

Explain the invoice result using ONLY the trusted data below.

Rules:
1. Do not invent facts, values, vendors, dates, invoices, or rules.
2. Do not change the decision.
3. If evidence is missing, say that it is missing.
4. Cite only rule IDs and evidence keys present in the trusted data.
5. Return JSON only.

Trusted data:
{json.dumps(trusted_data, indent=2, allow_nan=False)}

Return this exact JSON structure:
{{
  "explanation": "Short explanation for a human reviewer.",
  "cited_rule_ids": ["RULE_ID"],
  "cited_evidence_keys": ["vendor", "amount"]
}}
"""


def validate_ai_citations(ai_response, trusted_explanation):
    allowed_rule_ids = set(trusted_explanation.get("rule_ids", []))
    allowed_evidence_keys = set(
        trusted_explanation.get("evidence_used", {}).keys()
    )

    cited_rules = set(ai_response.get("cited_rule_ids", []))
    cited_keys = set(ai_response.get("cited_evidence_keys", []))

    unsupported_rules = cited_rules - allowed_rule_ids
    unsupported_keys = cited_keys - allowed_evidence_keys

    if unsupported_rules or unsupported_keys:
        raise ValueError(
            "Unsupported AI citations found: "
            f"rules={sorted(unsupported_rules)}, "
            f"evidence={sorted(unsupported_keys)}"
        )

    return True


if __name__ == "__main__":
    df = pd.read_csv("data/invoices.csv")

    for rule_result in process_invoices(df):
        explanation = create_structured_explanation(rule_result)
        routed_result = add_confidence_and_routing(explanation)

        if routed_result["decision"] == "flagged":
            prompt = create_evidence_only_prompt(routed_result)
            print(prompt)
            sample_ai_response = {
                "explanation": (
                    "Invoice INV002 is flagged because its amount is "
                    "15000.0, which exceeds the Equipment limit of 10000."
                ),
                "cited_rule_ids": ["AMOUNT_LIMIT"],
                "cited_evidence_keys": ["amount", "category"]
            }

            is_valid = validate_ai_citations(
                sample_ai_response,
                routed_result
            )

            print("AI citations valid:", is_valid)
            break