import json


MATCH_FIELDS = ("vendor", "amount", "date")


def duplicate_explanation(invoice, matched_invoice):
    """Return a structured explanation using only values in two invoice records."""
    missing = [
        field
        for field in ("invoice_id", *MATCH_FIELDS)
        if field not in invoice or field not in matched_invoice
    ]
    if missing:
        raise ValueError(f"Both invoice records need these fields: {', '.join(missing)}")

    matching_fields = [
        field for field in MATCH_FIELDS if invoice[field] == matched_invoice[field]
    ]
    evidence_used = [
        {
            "field": field,
            "current_invoice_value": invoice[field],
            "matched_invoice_value": matched_invoice[field],
        }
        for field in matching_fields
    ]

    if matching_fields:
        readable_fields = ", ".join(matching_fields)
        explanation = (
            f"Invoice {invoice['invoice_id']} may duplicate invoice "
            f"{matched_invoice['invoice_id']}. Both records match on: {readable_fields}."
        )
    else:
        explanation = (
            f"Invoice {invoice['invoice_id']} does not match invoice "
            f"{matched_invoice['invoice_id']} on vendor, amount, or date."
        )

    return {
        "decision": "flagged" if matching_fields else "passed",
        "summary": "Possible duplicate invoice" if matching_fields else "No duplicate evidence",
        "explanation": explanation,
        "evidence_used": evidence_used,
        "matched_invoice_id": matched_invoice["invoice_id"],
        "confidence": round(len(matching_fields) / len(MATCH_FIELDS), 2),
        "human_review_required": bool(matching_fields),
        "review_reason": "Duplicate-invoice evidence found" if matching_fields else None,
        "rule_ids": ["DUPLICATE_INVOICE"] if matching_fields else [],
    }


if __name__ == "__main__":
    current_invoice = {
        "invoice_id": "INV-1042",
        "vendor": "Acme Supplies",
        "amount": 18500,
        "date": "2026-09-17",
    }
    previous_invoice = {
        "invoice_id": "INV-0987",
        "vendor": "Acme Supplies",
        "amount": 18500,
        "date": "2026-09-17",
    }

    result = duplicate_explanation(current_invoice, previous_invoice)
    print(json.dumps(result, indent=2))
