"""Pure helpers for filtering and exporting FinSight results."""
from __future__ import annotations
import pandas as pd

VIEWS = ("All", "Auto-pass", "Exceptions", "Human review")

def filter_results(df: pd.DataFrame, query: str = "", view: str = "All") -> pd.DataFrame:
    out = df
    if view == "Auto-pass":
        out = out[out["route"] == "AUTO_PASS"]
    elif view == "Exceptions":
        out = out[out["status"] == "EXCEPTION"]
    elif view == "Human review":
        out = out[out["human_review_required"].astype(bool)]
    query = (query or "").strip().casefold()
    if query and not out.empty:
        haystack = out.fillna("").astype(str).agg(" ".join, axis=1).str.casefold()
        out = out[haystack.str.contains(query, regex=False)]
    return out

def view_counts(df: pd.DataFrame) -> dict[str, int]:
    return {view: len(filter_results(df, "", view)) for view in VIEWS}

def attach_reviews(df: pd.DataFrame, reviews: dict[str, dict]) -> pd.DataFrame:
    out = df.copy()
    ids = out["invoice_id"].astype(str)
    out["reviewer_decision"] = ids.map(lambda i: reviews.get(i, {}).get("action", ""))
    out["reviewer_comment"] = ids.map(lambda i: reviews.get(i, {}).get("comment", ""))
    return out
