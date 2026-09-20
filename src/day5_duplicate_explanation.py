import json


def create_duplicate_explanation(invoice, matched_invoice):
    evidence = []

    for field in ["vendor", "amount", "category", "invoice_date"]:
        if invoice.get(field) == matched_invoice.get(field):
            evidence.append({
                "field": field,
                "invoice_value": invoice.get(field),
                "matched_invoice_value": matched_invoice.get(field)
            })

    if not evidence:
        return {
            "decision": "passed",
            "summary": "No duplicate evidence found.",
            "explanation": "The two invoices do not match on the checked fields.",
            "evidence_used": [],
            "human_review_required": False
        }

    fields = ", ".join(item["field"] for item in evidence)

    return {
        "decision": "flagged",
        "summary": "Possible duplicate invoice.",
        "explanation": (
            f"Invoice {invoice['invoice_id']} may duplicate "
            f"{matched_invoice['invoice_id']}. Both records match on: {fields}."
        ),
        "evidence_used": evidence,
        "matched_invoice_id": matched_invoice["invoice_id"],
        "human_review_required": True,
        "review_reason": "Duplicate-invoice evidence found.",
        "rule_ids": ["DUPLICATE_INVOICE"]
    }


if __name__ == "__main__":
    invoice = {
        "invoice_id": "INV001",
        "vendor": "ABC Suppliers",
        "amount": 4500,
        "category": "Travel",
        "invoice_date": "2026-09-14"
    }

    matched_invoice = {
        "invoice_id": "INV003",
        "vendor": "ABC Suppliers",
        "amount": 4500,
        "category": "Travel",
        "invoice_date": "2026-09-14"
    }

    print(json.dumps(
        create_duplicate_explanation(invoice, matched_invoice),
        indent=2
    ))