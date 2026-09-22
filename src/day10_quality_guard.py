import json
import pandas as pd

from src.rule_engine import process_invoices
from src.day6_structured_explanation import (
    create_structured_explanation,
)
from src.day7_routing import add_confidence_and_routing
from src.day8_evidence_prompt import validate_ai_citations
from src.day9_ai_explainer import generate_ai_explanation


def template_result(trusted, reason):
    return {
        "invoice_id": trusted["invoice_id"],
        "decision": trusted["decision"],
        "explanation": trusted["explanation"],
        "evidence_used": trusted.get("evidence_used", {}),
        "rule_ids": trusted.get("rule_ids", []),
        "confidence": trusted.get("confidence"),
        "route": trusted.get("route"),
        "mode": "quality_guard_fallback",
        "reason": reason,
    }


def create_quality_checked_result(trusted, ai_response):
    try:
        explanation_text = ai_response.get("explanation", "").strip()

        if not explanation_text:
            raise ValueError("AI explanation is empty.")

        if len(explanation_text) > 400:
            raise ValueError("AI explanation is too long.")

        validate_ai_citations(ai_response, trusted)

        cited_keys = ai_response.get("cited_evidence_keys", [])
        trusted_evidence = trusted.get("evidence_used", {})

        cited_evidence = {
            key: trusted_evidence[key]
            for key in cited_keys
        }

        if not explanation_text.endswith((".", "!", "?")):
            explanation_text += "."

        return {
            "invoice_id": trusted["invoice_id"],
            "decision": trusted["decision"],
            "explanation": explanation_text,
            "evidence_used": cited_evidence,
            "rule_ids": trusted.get("rule_ids", []),
            "confidence": trusted.get("confidence"),
            "route": trusted.get("route"),
            "mode": ai_response.get("mode", "ai_response"),
            "quality_checked": True,
        }

    except (KeyError, TypeError, ValueError) as error:
        return template_result(trusted, str(error))


if __name__ == "__main__":
    df = pd.read_csv("data/invoices.csv")

    for rule_result in process_invoices(df):
        structured = create_structured_explanation(rule_result)
        trusted = add_confidence_and_routing(structured)

        if trusted["decision"] == "flagged":
            ai_response = generate_ai_explanation(trusted)

            result = create_quality_checked_result(
                trusted,
                ai_response
            )

            print(json.dumps(
                result,
                indent=2,
                allow_nan=False
            ))
            break