"""Day 10 — quality guard.

Takes the (possibly AI-generated) explanation and the trusted, deterministic
result it was generated from, and makes sure the AI did not invent facts,
change the decision, or go on for too long. If anything looks wrong, it
falls back to the plain rule-engine explanation instead of showing the
person something untrustworthy.
"""
from __future__ import annotations

from typing import Any

from src.day8_evidence_prompt import validate_ai_citations


def template_result(trusted: dict[str, Any], reason: str) -> dict[str, Any]:
    """Safe fallback: the deterministic explanation, unchanged, with a note why."""
    return {
        "invoice_id": trusted.get("invoice_id"),
        "decision": trusted.get("decision"),
        "explanation": trusted.get("explanation", "No explanation available."),
        "evidence_used": trusted.get("evidence_used", {}),
        "rule_ids": trusted.get("rule_ids", []),
        "confidence": trusted.get("confidence"),
        "uncertainty": trusted.get("uncertainty"),
        "route": trusted.get("route"),
        "human_review_required": trusted.get("human_review_required", False),
        "review_reason": trusted.get("review_reason"),
        "rule_details": trusted.get("rule_details", []),
        "matched_invoice_ids": trusted.get("matched_invoice_ids", []),
        "mode": "quality_guard_fallback",
        "quality_checked": True,
        "fallback_reason": reason,
    }


def create_quality_checked_result(
    trusted: dict[str, Any], ai_response: dict[str, Any]
) -> dict[str, Any]:
    """Validate an AI explanation against the trusted evidence, or fall back."""
    try:
        explanation_text = str(ai_response.get("explanation", "")).strip()

        if not explanation_text:
            raise ValueError("AI explanation is empty.")

        if len(explanation_text) > 400:
            raise ValueError("AI explanation is too long.")

        validate_ai_citations(ai_response, trusted)

        cited_keys = ai_response.get("cited_evidence_keys", [])
        trusted_evidence = trusted.get("evidence_used", {})
        cited_evidence = {
            key: trusted_evidence[key] for key in cited_keys if key in trusted_evidence
        }

        if not explanation_text.endswith((".", "!", "?")):
            explanation_text += "."

        return {
            "invoice_id": trusted.get("invoice_id"),
            "decision": trusted.get("decision"),
            "explanation": explanation_text,
            "evidence_used": cited_evidence,
            "rule_ids": trusted.get("rule_ids", []),
            "confidence": trusted.get("confidence"),
            "uncertainty": trusted.get("uncertainty"),
            "route": trusted.get("route"),
            "human_review_required": trusted.get("human_review_required", False),
            "review_reason": trusted.get("review_reason"),
            "rule_details": trusted.get("rule_details", []),
            "matched_invoice_ids": trusted.get("matched_invoice_ids", []),
            "mode": ai_response.get("mode", "ai_response"),
            "quality_checked": True,
        }

    except (KeyError, TypeError, ValueError) as error:
        return template_result(trusted, str(error))
