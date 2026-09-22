import json
import os

import pandas as pd

from src.rule_engine import process_invoices
from src.day6_structured_explanation import (
    create_structured_explanation,
)
from src.day7_routing import add_confidence_and_routing
from src.day8_evidence_prompt import (
    create_evidence_only_prompt,
    validate_ai_citations,
)


def template_fallback(explanation, reason):
    return {
        "explanation": explanation["explanation"],
        "cited_rule_ids": explanation["rule_ids"],
        "cited_evidence_keys": list(
            explanation.get("evidence_used", {}).keys()
        ),
        "mode": "template_fallback",
        "fallback_reason": reason,
    }


def generate_ai_explanation(explanation):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return template_fallback(
            explanation,
            "GEMINI_API_KEY is not configured."
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = create_evidence_only_prompt(explanation)

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )

        ai_response = json.loads(response.text)

        validate_ai_citations(ai_response, explanation)

        ai_response["mode"] = "gemini_api"
        return ai_response

    except Exception as error:
        return template_fallback(explanation, str(error))


if __name__ == "__main__":
    df = pd.read_csv("data/invoices.csv")

    for rule_result in process_invoices(df):
        structured = create_structured_explanation(rule_result)
        routed = add_confidence_and_routing(structured)

        if routed["decision"] == "flagged":
            result = generate_ai_explanation(routed)

            print(json.dumps(
                result,
                indent=2,
                allow_nan=False
            ))
            break