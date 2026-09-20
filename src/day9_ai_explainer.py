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


def parse_ai_json(text):
    text = text.strip()

    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0].strip()

    return json.loads(text)


def generate_ai_explanation(explanation):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return template_fallback(
            explanation,
            "OPENAI_API_KEY is not configured."
        )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        prompt = create_evidence_only_prompt(explanation)

        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-6-astra"),
            input=prompt,
        )

        ai_response = parse_ai_json(response.output_text)

        validate_ai_citations(ai_response, explanation)

        ai_response["mode"] = "openai_api"
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