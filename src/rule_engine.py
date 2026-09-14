import pandas as pd

from config import CATEGORY_LIMITS, REQUIRED_COLUMNS


def process_invoices(df: pd.DataFrame) -> list:
    """
    Accepts a pandas DataFrame and returns standard invoice results.
    """

    results = []
    seen_ids = set()

    for _, invoice in df.iterrows():
        reasons = []

        invoice_id = invoice.get("invoice_id")
        vendor = invoice.get("vendor")
        amount = invoice.get("amount")
        category = invoice.get("category")
        invoice_date = invoice.get("invoice_date")

        if invoice_id in seen_ids:
            reasons.append({
                "rule": "DUPLICATE_INVOICE_ID",
                "message": "Invoice ID already exists",
                "actual_value": invoice_id,
                "expected_value": "Unique invoice ID"
            })

        seen_ids.add(invoice_id)

        if pd.isna(vendor) or str(vendor).strip() == "":
            reasons.append({
                "rule": "MISSING_VENDOR",
                "message": "Vendor is missing",
                "actual_value": vendor,
                "expected_value": "Vendor name"
            })

        if pd.isna(amount) or amount <= 0:
            reasons.append({
                "rule": "INVALID_AMOUNT",
                "message": "Amount must be greater than zero",
                "actual_value": amount,
                "expected_value": "Amount greater than zero"
            })

        limit = CATEGORY_LIMITS.get(category)

        if limit is not None and amount > limit:
            reasons.append({
                "rule": "AMOUNT_LIMIT",
                "message": "Amount exceeds category limit",
                "actual_value": amount,
                "expected_value": limit
            })

        results.append({
            "invoice_id": invoice_id,
            "status": "CLEAN" if not reasons else "EXCEPTION",
            "reasons": reasons,
            "evidence": {
                "vendor": vendor,
                "amount": amount,
                "category": category,
                "invoice_date": invoice_date
            }
        })

    return results