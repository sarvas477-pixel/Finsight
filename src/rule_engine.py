import pandas as pd

from src.config import CATEGORY_LIMITS, REQUIRED_COLUMNS


def _is_missing(value):
    """Return True for None, NaN, or blank strings."""
    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass

    return isinstance(value, str) and value.strip() == ""


def _normalise_text(value):
    if _is_missing(value):
        return None

    return str(value).strip().casefold()


def _normalise_date(value):
    if _is_missing(value):
        return None

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return str(value).strip()

    return parsed.strftime("%Y-%m-%d")


def _duplicate_match(invoice, previous):
    """
    Detect an exact content duplicate using:
    vendor + amount + invoice_date
    """

    vendor_a = _normalise_text(invoice.get("vendor"))
    vendor_b = _normalise_text(previous.get("vendor"))

    date_a = _normalise_date(invoice.get("invoice_date"))
    date_b = _normalise_date(previous.get("invoice_date"))

    if vendor_a is None or vendor_b is None:
        return False

    if date_a is None or date_b is None:
        return False

    try:
        amount_a = float(invoice.get("amount"))
        amount_b = float(previous.get("amount"))
    except (TypeError, ValueError):
        return False

    return (
        vendor_a == vendor_b
        and amount_a == amount_b
        and date_a == date_b
    )


def process_invoices(df: pd.DataFrame) -> list:
    """
    Validate invoices and return structured results.

    Rules:
    1. Required fields
    2. Duplicate invoice ID
    3. Invalid amount
    4. Unknown category
    5. Category spending limit
    6. Content duplicate
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("process_invoices expects a pandas DataFrame")

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required CSV columns: "
            + ", ".join(missing_columns)
        )

    results = []

    seen_ids = {}
    previous_invoices = []

    for _, invoice in df.iterrows():

        reasons = []

        invoice_id = invoice.get("invoice_id")
        vendor = invoice.get("vendor")
        amount = invoice.get("amount")
        category = invoice.get("category")
        invoice_date = invoice.get("invoice_date")

        values = {
            "invoice_id": invoice_id,
            "vendor": vendor,
            "amount": amount,
            "category": category,
            "invoice_date": invoice_date,
        }

        # --------------------------------
        # 1. Required fields
        # --------------------------------

        for field in REQUIRED_COLUMNS:

            value = values[field]

            if _is_missing(value):

                reasons.append({
                    "rule": "MISSING_REQUIRED_FIELD",
                    "message": f"{field} is missing",
                    "actual_value": None,
                    "expected_value": f"{field} must be provided",
                })

        # --------------------------------
        # 2. Duplicate invoice ID
        # --------------------------------

        normalised_id = _normalise_text(invoice_id)

        if (
            normalised_id is not None
            and normalised_id in seen_ids
        ):

            reasons.append({
                "rule": "DUPLICATE_INVOICE_ID",
                "message": "Invoice ID already exists",
                "actual_value": invoice_id,
                "expected_value": "Unique invoice ID",
                "matched_invoice_id": seen_ids[normalised_id],
            })

        elif normalised_id is not None:

            seen_ids[normalised_id] = invoice_id

        # --------------------------------
        # 3. Amount validation
        # --------------------------------

        numeric_amount = None

        if not _is_missing(amount):

            try:

                numeric_amount = float(amount)

                if numeric_amount <= 0:

                    reasons.append({
                        "rule": "INVALID_AMOUNT",
                        "message": "Amount must be greater than zero",
                        "actual_value": numeric_amount,
                        "expected_value": "Amount greater than zero",
                    })

            except (ValueError, TypeError):

                reasons.append({
                    "rule": "INVALID_AMOUNT",
                    "message": "Amount must be a valid number",
                    "actual_value": amount,
                    "expected_value": "Numeric amount",
                })

        # --------------------------------
        # 4. Unknown category
        # --------------------------------

        normalised_category = _normalise_text(category)

        category_key = next(
            (
                key
                for key in CATEGORY_LIMITS
                if _normalise_text(key) == normalised_category
            ),
            None,
        )

        if (
            not _is_missing(category)
            and category_key is None
        ):

            reasons.append({
                "rule": "UNKNOWN_CATEGORY",
                "message": "Category is not configured",
                "actual_value": category,
                "expected_value": sorted(
                    CATEGORY_LIMITS.keys()
                ),
            })

        # --------------------------------
        # 5. Category amount limit
        # --------------------------------

        if (
            numeric_amount is not None
            and category_key is not None
        ):

            limit = CATEGORY_LIMITS[category_key]

            if numeric_amount > limit:

                reasons.append({
                    "rule": "AMOUNT_LIMIT",
                    "message": "Amount exceeds category limit",
                    "actual_value": numeric_amount,
                    "expected_value": limit,
                })

        # --------------------------------
        # 6. Content duplicate
        # --------------------------------

        matched_invoice_id = None

        for previous in previous_invoices:

            if _duplicate_match(values, previous):

                matched_invoice_id = previous.get(
                    "invoice_id"
                )

                reasons.append({
                    "rule": "DUPLICATE_INVOICE",
                    "message": (
                        "Possible duplicate: vendor, amount, "
                        "and invoice date match another invoice"
                    ),
                    "actual_value": {
                        "vendor": vendor,
                        "amount": numeric_amount,
                        "invoice_date": invoice_date,
                    },
                    "expected_value": (
                        "No invoice with the same vendor, "
                        "amount, and date"
                    ),
                    "matched_invoice_id": matched_invoice_id,
                    "human_review_required": True,
                })

                break

        current_record = values.copy()

        current_record["amount"] = (
            numeric_amount
            if numeric_amount is not None
            else amount
        )

        previous_invoices.append(current_record)

        # --------------------------------
        # Final result
        # --------------------------------

        results.append({
            "invoice_id": invoice_id,

            "status": (
                "CLEAN"
                if not reasons
                else "EXCEPTION"
            ),

            "reasons": reasons,

            "evidence": {
                "vendor": vendor,
                "amount": (
                    numeric_amount
                    if numeric_amount is not None
                    else amount
                ),
                "category": category,
                "invoice_date": invoice_date,
                "matched_invoice_id": matched_invoice_id,
            },
        })

    return results


if __name__ == "__main__":

    df = pd.read_csv("data/invoices.csv")

    results = process_invoices(df)

    for result in results:
        print(result)