import math
from typing import Any
import pandas as pd
from src.config import CATEGORY_LIMITS, REQUIRED_COLUMNS

def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and value.strip() == ""

def _normalise_text(value: Any):
    if _is_missing(value):
        return None
    return str(value).strip().casefold()

def _parse_amount(value: Any):
    if _is_missing(value):
        return None
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None

def _normalise_date(value: Any):
    if _is_missing(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.strftime("%Y-%m-%d")

def validate_dataframe(df: pd.DataFrame) -> None:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("process_invoices expects a pandas DataFrame")
    if df.columns.duplicated().any():
        duplicates = df.columns[df.columns.duplicated()].tolist()
        raise ValueError("Duplicate CSV columns found: " + ", ".join(map(str, duplicates)))
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("Missing required CSV columns: " + ", ".join(missing))
    if df.empty:
        raise ValueError("The CSV contains no invoice rows.")

def _duplicate_match(current, previous):
    return (
        _normalise_text(current.get("vendor")) is not None
        and _normalise_text(previous.get("vendor")) == _normalise_text(current.get("vendor"))
        and _parse_amount(current.get("amount")) is not None
        and _parse_amount(previous.get("amount")) == _parse_amount(current.get("amount"))
        and _normalise_date(current.get("invoice_date")) is not None
        and _normalise_date(previous.get("invoice_date")) == _normalise_date(current.get("invoice_date"))
    )

def process_invoices(df: pd.DataFrame) -> list[dict]:
    validate_dataframe(df)
    results, seen_ids, previous = [], {}, []
    for _, row in df.iterrows():
        values = {c: row.get(c) for c in REQUIRED_COLUMNS}
        reasons = []
        for field in REQUIRED_COLUMNS:
            if _is_missing(values[field]):
                reasons.append({
                    "rule": "MISSING_REQUIRED_FIELD",
                    "message": f"{field} is missing.",
                    "actual_value": None,
                    "expected_value": f"{field} must be provided.",
                    "human_review_required": True,
                })

        iid_norm = _normalise_text(values["invoice_id"])
        if iid_norm is not None and iid_norm in seen_ids:
            matched = seen_ids[iid_norm]
            reasons.append({
                "rule": "DUPLICATE_INVOICE_ID",
                "message": "Invoice ID already exists.",
                "actual_value": values["invoice_id"],
                "expected_value": "Unique invoice ID.",
                "matched_invoice_id": matched,
                "matched_invoice_ids": [matched],
                "human_review_required": True,
            })
        elif iid_norm is not None:
            seen_ids[iid_norm] = values["invoice_id"]

        amount = _parse_amount(values["amount"])
        if not _is_missing(values["amount"]):
            if amount is None or amount <= 0:
                reasons.append({
                    "rule": "INVALID_AMOUNT",
                    "message": "Amount must be a finite number greater than zero.",
                    "actual_value": values["amount"],
                    "expected_value": "> 0",
                    "human_review_required": True,
                })

        date = _normalise_date(values["invoice_date"])
        if not _is_missing(values["invoice_date"]) and date is None:
            reasons.append({
                "rule": "INVALID_DATE",
                "message": "Invoice date is invalid.",
                "actual_value": values["invoice_date"],
                "expected_value": "A valid date.",
                "human_review_required": True,
            })

        cat_norm = _normalise_text(values["category"])
        category_key = next((k for k in CATEGORY_LIMITS if _normalise_text(k) == cat_norm), None)
        if not _is_missing(values["category"]) and category_key is None:
            reasons.append({
                "rule": "UNKNOWN_CATEGORY",
                "message": "Category is not configured.",
                "actual_value": values["category"],
                "expected_value": sorted(CATEGORY_LIMITS),
                "human_review_required": True,
            })

        if amount is not None and amount > 0 and category_key is not None:
            limit = CATEGORY_LIMITS[category_key]
            if amount > limit:
                reasons.append({
                    "rule": "AMOUNT_LIMIT",
                    "message": f"Amount exceeds the {category_key} category limit.",
                    "actual_value": amount,
                    "expected_value": limit,
                    "human_review_required": True,
                })

        matched_ids = []
        current = values.copy()
        for old in previous:
            if _duplicate_match(current, old):
                mid = old.get("invoice_id")
                matched_ids.append(mid)
                reasons.append({
                    "rule": "DUPLICATE_INVOICE",
                    "message": "Possible duplicate: vendor, amount, and invoice date match another invoice.",
                    "actual_value": {
                        "vendor": values["vendor"],
                        "amount": amount,
                        "invoice_date": date,
                    },
                    "expected_value": "No invoice with the same vendor, amount, and date.",
                    "matched_invoice_id": mid,
                    "matched_invoice_ids": [mid],
                    "human_review_required": True,
                })
                break

        previous.append({
            **values,
            "amount": amount,
            "invoice_date": date,
        })

        status = "CLEAN" if not reasons else "EXCEPTION"
        review = any(r.get("human_review_required", False) for r in reasons)
        rule_ids = [r["rule"] for r in reasons]
        if not reasons:
            confidence = 1.0
        elif any(r["rule"] == "DUPLICATE_INVOICE" for r in reasons):
            confidence = 0.80
        elif any(r["rule"] == "MISSING_REQUIRED_FIELD" for r in reasons):
            confidence = 0.95
        else:
            confidence = 0.99
        route = "HUMAN_REVIEW" if review else ("AUTO_PASS" if status == "CLEAN" else "EXCEPTION")
        evidence = {
            "invoice_id": values["invoice_id"],
            "vendor": values["vendor"],
            "amount": amount if amount is not None else values["amount"],
            "category": values["category"],
            "invoice_date": date if date is not None else values["invoice_date"],
            "matched_invoice_id": matched_ids[0] if matched_ids else None,
            "matched_invoice_ids": matched_ids,
        }
        results.append({
            "invoice_id": values["invoice_id"],
            "status": status,
            "route": route,
            "confidence": confidence,
            "human_review_required": review,
            "rule_ids": rule_ids,
            "reasons": reasons,
            "evidence": evidence,
        })
    # Optional deep-learning layer. It is deliberately disabled for tiny batches
    # so the existing deterministic behavior remains stable for sample/demo data.
    if len(df) >= 8:
        try:
            from src.deep_learning import score_invoices
            normal_mask = pd.Series([r["status"] == "CLEAN" for r in results], index=df.index)
            dl_results = score_invoices(df, CATEGORY_LIMITS, normal_mask=normal_mask)
            for result, dl in zip(results, dl_results):
                result["dl_available"] = dl.available
                result["dl_anomaly_score"] = round(float(dl.score), 4)
                result["dl_status"] = dl.status
                result["dl_reconstruction_error"] = round(float(dl.reconstruction_error), 6)
                result["dl_reason"] = dl.reason
                if dl.available and dl.status == "ANOMALY":
                    result["rule_ids"].append("DL_ANOMALY")
                    result["reasons"].append({
                        "rule": "DL_ANOMALY",
                        "message": dl.reason,
                        "actual_value": round(float(dl.score), 4),
                        "expected_value": "Neural anomaly score below 0.65.",
                        "human_review_required": True,
                    })
                    result["status"] = "EXCEPTION"
                    result["route"] = "HUMAN_REVIEW"
                    result["human_review_required"] = True
                    result["confidence"] = min(float(result["confidence"]), max(0.05, 1.0 - float(dl.score)))
        except Exception:
            # Deep learning is advisory. A missing/broken optional ML stack
            # must never make the deterministic invoice analysis fail.
            for result in results:
                result.setdefault("dl_available", False)
                result.setdefault("dl_anomaly_score", 0.0)
                result.setdefault("dl_status", "UNAVAILABLE")
                result.setdefault("dl_reconstruction_error", 0.0)
                result.setdefault("dl_reason", "Deep-learning detector unavailable.")
    else:
        for result in results:
            result["dl_available"] = False
            result["dl_anomaly_score"] = 0.0
            result["dl_status"] = "UNAVAILABLE"
            result["dl_reconstruction_error"] = 0.0
            result["dl_reason"] = "Deep-learning detector requires at least 8 invoices."

    return results

def summarize_results(results):
    return {
        "total": len(results),
        "clean": sum(r["status"] == "CLEAN" for r in results),
        "exceptions": sum(r["status"] == "EXCEPTION" for r in results),
        "review_required": sum(r["human_review_required"] for r in results),
    }
