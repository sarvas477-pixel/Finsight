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

            # Summary
            total = len(results)
            exceptions = sum(
                r["status"] == "EXCEPTION"
                for r in results
            )
            clean = total - exceptions

            col1, col2, col3 = st.columns(3)

            col1.metric("Total Invoices", total)
            col2.metric("Clean", clean)
            col3.metric("Exceptions", exceptions)

            st.divider()

            # Results table
            result_table = []

            for r in results:

                reason_text = "; ".join(
                    reason["message"]
                    for reason in r["reasons"]
                )

                matched_id = ""

                for reason in r["reasons"]:
                    if reason.get("matched_invoice_id"):
                        matched_id = reason["matched_invoice_id"]
                        break

                result_table.append({
                    "Invoice ID": r["invoice_id"],
                    "Status": r["status"],
                    "Reason": reason_text,
                    "Matched Invoice": matched_id
                })

            results_df = pd.DataFrame(result_table)

            st.subheader("Validation Results")
            st.dataframe(
                results_df,
                use_container_width=True
            )

            # Exceptions
            exception_results = [
                r for r in results
                if r["status"] == "EXCEPTION"
            ]

            if exception_results:

                st.subheader("⚠️ Exceptions")

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

                st.success("All invoices passed validation! 🎉")