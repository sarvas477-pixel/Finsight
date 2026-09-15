import pandas as pd

from config import CATEGORY_LIMITS, REQUIRED_COLUMNS

def process_invoices(df: pd.DataFrame) -> list:
    """
    Checks invoices and returns structured results.
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

        # 1. Check required fields
        values = {
            "invoice_id": invoice_id,
            "vendor": vendor,
            "amount": amount,
            "category": category,
            "invoice_date": invoice_date
        }

        for field in REQUIRED_COLUMNS:
            value = values.get(field)

            if pd.isna(value) or str(value).strip() == "":
                reasons.append({
                    "rule": "MISSING_REQUIRED_FIELD",
                    "message": f"{field} is missing",
                    "actual_value": value,
                    "expected_value": f"{field} must be provided"
                })

        # 2. Check duplicate invoice ID
        if invoice_id in seen_ids:
            reasons.append({
                "rule": "DUPLICATE_INVOICE_ID",
                "message": "Invoice ID already exists",
                "actual_value": invoice_id,
                "expected_value": "Unique invoice ID"
            })

        if not pd.isna(invoice_id):
            seen_ids.add(invoice_id)

        # 3. Check amount
        if not pd.isna(amount):
            try:
                amount = float(amount)

                if amount <= 0:
                    reasons.append({
                        "rule": "INVALID_AMOUNT",
                        "message": "Amount must be greater than zero",
                        "actual_value": amount,
                        "expected_value": "Amount greater than zero"
                    })

                # 4. Check category limit
                limit = CATEGORY_LIMITS.get(category)

                if limit is not None and amount > limit:
                    reasons.append({
                        "rule": "AMOUNT_LIMIT",
                        "message": "Amount exceeds category limit",
                        "actual_value": amount,
                        "expected_value": limit
                    })

            except (ValueError, TypeError):
                reasons.append({
                    "rule": "INVALID_AMOUNT",
                    "message": "Amount must be a valid number",
                    "actual_value": amount,
                    "expected_value": "Numeric amount"
                })

        # Final result
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


# Run directly from terminal
if __name__ == "__main__":
    df = pd.read_csv("data/invoices.csv")

    results = process_invoices(df)

    for result in results:
        print(result)