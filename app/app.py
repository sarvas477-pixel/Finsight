import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

from src.config import CATEGORY_LIMITS, REQUIRED_COLUMNS
from src.rule_engine import process_invoices


st.set_page_config(
    page_title="Finsight - Invoice Checker",
    layout="wide"
)

REVIEW_STATUS_VALUE = "REVIEW"

st.title("🧾 Finsight")
st.subheader("Invoice & Expense Exception Checker")

st.write(
    "Upload an invoice CSV and Finsight will check it for "
    "missing fields, duplicate invoices, invalid amounts, "
    "category limits, and other exceptions."
)

st.divider()

uploaded_file = st.file_uploader(
    "Upload Invoice CSV",
    type=["csv"]
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    st.success(f"Uploaded {len(df)} invoices")

    # Check required columns
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        st.error(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    else:

        st.subheader("Uploaded Invoices")
        st.dataframe(df, use_container_width=True)

        if st.button("🔍 Check Invoices"):

            with st.spinner("Processing invoices..."):

                results = process_invoices(df)

            # --- Sort every invoice into one of three piles ---
            # NOTE: this assumes M1/M2's status field uses exactly these
            # three values: "CLEAN", "EXCEPTION", and REVIEW_STATUS_VALUE
            # (set near the top of this file). If a result doesn't match
            # any of the three, it falls into "Auto-Passed" by default —
            # confirm with M1/M2 whether that's the right fallback.

            auto_pass_results = [
                r for r in results
                if r["status"] not in ("EXCEPTION", REVIEW_STATUS_VALUE)
            ]
            exception_results = [
                r for r in results
                if r["status"] == "EXCEPTION"
            ]
            review_results = [
                r for r in results
                if r["status"] == REVIEW_STATUS_VALUE
            ]

            # Summary
            total = len(results)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Invoices", total)
            col2.metric("✅ Auto-Passed", len(auto_pass_results))
            col3.metric("⚠️ Exceptions", len(exception_results))
            col4.metric("🤔 Needs Review", len(review_results))

            st.divider()

            def badge_for(status):
                """Turn a raw status string into an emoji badge label."""
                if status == "EXCEPTION":
                    return "⚠️ Exception"
                if status == REVIEW_STATUS_VALUE:
                    return "🤔 Needs Review"
                return "✅ Clean"

            def build_table(result_list):
                """Turn a list of result dicts into a display-ready table."""
                rows = []
                for r in result_list:
                    reason_text = "; ".join(
                        reason["message"]
                        for reason in r["reasons"]
                    )
                    matched_id = ""
                    for reason in r["reasons"]:
                        if reason.get("matched_invoice_id"):
                            matched_id = reason["matched_invoice_id"]
                            break
                    rows.append({
                        "Invoice ID": r["invoice_id"],
                        "Status": badge_for(r["status"]),
                        "Reason": reason_text,
                        "Matched Invoice": matched_id
                    })
                return pd.DataFrame(rows)

            tab_pass, tab_exceptions, tab_review = st.tabs([
                f"✅ Auto-Passed ({len(auto_pass_results)})",
                f"⚠️ Exceptions ({len(exception_results)})",
                f"🤔 Needs Review ({len(review_results)})"
            ])

            with tab_pass:
                if auto_pass_results:
                    st.dataframe(
                        build_table(auto_pass_results),
                        use_container_width=True
                    )
                else:
                    st.info("No invoices auto-passed.")

            with tab_exceptions:
                if exception_results:
                    st.dataframe(
                        build_table(exception_results),
                        use_container_width=True
                    )
                    st.divider()
                    for r in exception_results:
                        with st.expander(
                            f"{r['invoice_id']} — EXCEPTION"
                        ):
                            for reason in r["reasons"]:
                                st.write(
                                    f"**{reason['rule']}**: "
                                    f"{reason['message']}"
                                )
                                if reason.get("matched_invoice_id"):
                                    st.write(
                                        f"Matched Invoice: "
                                        f"{reason['matched_invoice_id']}"
                                    )
                else:
                    st.success("No exceptions found! 🎉")

            with tab_review:
                if review_results:
                    st.dataframe(
                        build_table(review_results),
                        use_container_width=True
                    )
                    st.divider()
                    for r in review_results:
                        with st.expander(
                            f"{r['invoice_id']} — NEEDS REVIEW"
                        ):
                            for reason in r["reasons"]:
                                st.write(
                                    f"**{reason['rule']}**: "
                                    f"{reason['message']}"
                                )
                                if reason.get("matched_invoice_id"):
                                    st.write(
                                        f"Matched Invoice: "
                                        f"{reason['matched_invoice_id']}"
                                    )
                else:
                    st.info("Nothing needs human review right now.")