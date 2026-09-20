import pandas as pd

from src.config import CATEGORY_LIMITS, REQUIRED_COLUMNS


def _is_missing(value):
    """Return True when a value is None, NaN, or blank."""
    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass

    return isinstance(value, str) and value.strip() == ""


def _normalise_text(value):
    """Normalize text for reliable comparisons."""
    if _is_missing(value):
        return None

    return str(value).strip().casefold()


def _parse_amount(value):
    """
    Convert amount to float.

    Returns:
        float value when valid
        None when missing or invalid
    """
    if _is_missing(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalise_date(value):
    """
    Convert a valid date to YYYY-MM-DD.

    Returns:
        normalized date string
        None when missing
        None when invalid
    """
    if _is_missing(value):
        return None

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed.strftime("%Y-%m-%d")


def _duplicate_match(invoice, previous):
    """
    Detect content duplicates using:

        vendor + amount + invoice_date

    Category is intentionally not part of the duplicate key.
    """

    vendor_a = _normalise_text(invoice.get("vendor"))
    vendor_b = _normalise_text(previous.get("vendor"))

    date_a = _normalise_date(invoice.get("invoice_date"))
    date_b = _normalise_date(previous.get("invoice_date"))

    amount_a = _parse_amount(invoice.get("amount"))
    amount_b = _parse_amount(previous.get("amount"))

    if vendor_a is None or vendor_b is None:
        return False

    if date_a is None or date_b is None:
        return False

    if amount_a is None or amount_b is None:
        return False

    return (
        vendor_a == vendor_b
        and amount_a == amount_b
        and date_a == date_b
    )


def process_invoices(df: pd.DataFrame) -> list:
    """
    Main deterministic FinSight rule engine.

    Input:
        pandas DataFrame containing invoice records.

    Output:
        list of structured decision results.

    Rules:
        1. Required fields
        2. Duplicate invoice ID
        3. Invalid amount
        4. Invalid date
        5. Unknown category
        6. Category spending limit
        7. Content duplicate
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "process_invoices expects a pandas DataFrame"
        )

    # --------------------------------------------------
    # 1. Validate required CSV columns
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Process every invoice
    # --------------------------------------------------

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

        # --------------------------------------------------
        # 2. Required fields
        # --------------------------------------------------

        for field in REQUIRED_COLUMNS:

            value = values[field]

            if _is_missing(value):

                reasons.append({
                    "rule": "MISSING_REQUIRED_FIELD",
                    "message": f"{field} is missing",
                    "actual_value": None,
                    "expected_value": f"{field} must be provided",
                    "human_review_required": True,
                })

        # --------------------------------------------------
        # 3. Duplicate invoice ID
        # --------------------------------------------------

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
                "human_review_required": True,
            })

        elif normalised_id is not None:

            seen_ids[normalised_id] = invoice_id

        # --------------------------------------------------
        # 4. Amount validation
        # --------------------------------------------------

        numeric_amount = _parse_amount(amount)

        if not _is_missing(amount):

            if numeric_amount is None:

                reasons.append({
                    "rule": "INVALID_AMOUNT",
                    "message": "Amount must be a valid number",
                    "actual_value": amount,
                    "expected_value": "Numeric amount",
                    "human_review_required": True,
                })

            elif numeric_amount <= 0:

                reasons.append({
                    "rule": "INVALID_AMOUNT",
                    "message": "Amount must be greater than zero",
                    "actual_value": numeric_amount,
                    "expected_value": "Amount greater than zero",
                    "human_review_required": True,
                })

        # --------------------------------------------------
        # 5. Date validation
        # --------------------------------------------------

        normalized_date = _normalise_date(invoice_date)

        if not _is_missing(invoice_date):

            if normalized_date is None:

                reasons.append({
                    "rule": "INVALID_DATE",
                    "message": "Invoice date is invalid",
                    "actual_value": invoice_date,
                    "expected_value": "Valid date",
                    "human_review_required": True,
                })

        # --------------------------------------------------
        # 6. Category validation
        # --------------------------------------------------

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
                "human_review_required": True,
            })

        # --------------------------------------------------
        # 7. Category spending limit
        # --------------------------------------------------

        if (
            numeric_amount is not None
            and numeric_amount > 0
            and category_key is not None
        ):

            limit = CATEGORY_LIMITS[category_key]

            if numeric_amount > limit:

                reasons.append({
                    "rule": "AMOUNT_LIMIT",
                    "message": "Amount exceeds category limit",
                    "actual_value": numeric_amount,
                    "expected_value": limit,
                    "human_review_required": True,
                })

        # --------------------------------------------------
        # 8. Content duplicate
        # --------------------------------------------------

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
                        "invoice_date": normalized_date,
                    },
                    "expected_value": (
                        "No invoice with the same vendor, "
                        "amount, and date"
                    ),
                    "matched_invoice_id": matched_invoice_id,
                    "human_review_required": True,
                })

                break

        # --------------------------------------------------
        # Save current invoice for future duplicate checks
        # --------------------------------------------------

        current_record = values.copy()

        current_record["amount"] = numeric_amount

        current_record["invoice_date"] = normalized_date

        previous_invoices.append(current_record)

        # --------------------------------------------------
        # 9. Final deterministic decision
        # --------------------------------------------------

        status = (
            "CLEAN"
            if not reasons
            else "EXCEPTION"
        )

        human_review_required = any(
            reason.get("human_review_required", False)
            for reason in reasons
        )

        rule_ids = [
            reason["rule"]
            for reason in reasons
        ]

        results.append({
            "invoice_id": invoice_id,

            "status": status,

            "human_review_required": human_review_required,

            "rule_ids": rule_ids,

            "reasons": reasons,

            "evidence": {
                "vendor": vendor,

                "amount": (
                    numeric_amount
                    if numeric_amount is not None
                    else amount
                ),

                "category": category,

                "invoice_date": (
                    normalized_date
                    if normalized_date is not None
                    else invoice_date
                ),

                "matched_invoice_id": matched_invoice_id,
            },
        })

    return results


def summarize_results(results):
    """
    Return simple deterministic summary statistics.
    """

    total = len(results)

    clean = sum(
        result["status"] == "CLEAN"
        for result in results
    )

    exceptions = sum(
        result["status"] == "EXCEPTION"
        for result in results
    )

    review_required = sum(
        result.get("human_review_required", False)
        for result in results
    )

    return {
        "total": total,
        "clean": clean,
        "exceptions": exceptions,
        "review_required": review_required,
    }


if __name__ == "__main__":

    df = pd.read_csv("data/invoices.csv")

    results = process_invoices(df)

    summary = summarize_results(results)

    print("\nFinSight Rule Engine")
    print("-" * 40)

    print(f"Total:          {summary['total']}")
    print(f"Clean:          {summary['clean']}")
    print(f"Exceptions:     {summary['exceptions']}")
    print(f"Review required:{summary['review_required']}")

    print("\nDetailed Results")
    print("-" * 40)

    for result in results:
        print(result)