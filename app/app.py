import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR)
    )

import pandas as pd
import streamlit as st

from src.config import REQUIRED_COLUMNS
from src.rule_engine import (
    process_invoices,
    summarize_results,
)
from src.day6_structured_explanation import (
    create_structured_explanation,
)
from src.day7_routing import (
    add_confidence_and_routing,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Finsight - Invoice Checker",
    page_icon="🧾",
    layout="wide",
)


# ============================================================
# HEADER
# ============================================================

st.title("🧾 Finsight")

st.subheader(
    "Invoice & Expense Exception Checker"
)

st.write(
    "Upload an invoice CSV and Finsight will check "
    "missing fields, duplicate invoices, invalid "
    "amounts, category limits, and other exceptions."
)

st.divider()


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Upload Invoice CSV",
    type=["csv"]
)


if uploaded_file is not None:

    # ========================================================
    # SAFE CSV READING
    # ========================================================

    try:

        df = pd.read_csv(
            uploaded_file
        )

    except pd.errors.EmptyDataError:

        st.error(
            "The uploaded CSV is empty."
        )

        st.stop()

    except pd.errors.ParserError:

        st.error(
            "The CSV file is malformed. "
            "Please check its columns and separators."
        )

        st.stop()

    except UnicodeDecodeError:

        st.error(
            "The CSV encoding could not be read. "
            "Please upload a UTF-8 CSV file."
        )

        st.stop()

    except Exception as error:

        st.error(
            f"Unable to read CSV: {error}"
        )

        st.stop()

    # ========================================================
    # EMPTY DATAFRAME
    # ========================================================

    if df.empty:

        st.warning(
            "The uploaded CSV contains no invoice rows."
        )

        st.stop()

    # ========================================================
    # REQUIRED COLUMNS
    # ========================================================

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        st.error(
            "Missing required columns: "
            + ", ".join(
                missing_columns
            )
        )

        st.stop()

    # ========================================================
    # UPLOAD SUCCESS
    # ========================================================

    st.success(
        f"Uploaded {len(df)} invoices."
    )

    # ========================================================
    # DATA PREVIEW
    # ========================================================

    with st.expander(
        "📄 View uploaded invoices",
        expanded=False
    ):

        st.dataframe(
            df,
            use_container_width=True
        )

    st.divider()

    # ========================================================
    # PROCESS
    # ========================================================

    if st.button(
        "🔍 Check Invoices",
        type="primary"
    ):

        with st.spinner(
            "Processing invoices..."
        ):

            try:

                results = process_invoices(
                    df
                )

            except Exception as error:

                st.error(
                    f"Rule engine error: {error}"
                )

                st.stop()

        # ====================================================
        # SUMMARY
        # ====================================================

        summary = summarize_results(
            results
        )

        total = summary["total"]

        clean_results = [
            result
            for result in results
            if result["status"] == "CLEAN"
        ]

        exception_results = [
            result
            for result in results
            if (
                result["status"] == "EXCEPTION"
                and not result.get(
                    "human_review_required",
                    False
                )
            )
        ]

        review_results = [
            result
            for result in results
            if (
                result["status"] == "EXCEPTION"
                and result.get(
                    "human_review_required",
                    False
                )
            )
        ]

        # ====================================================
        # METRICS
        # ====================================================

        col1, col2, col3, col4 = (
            st.columns(4)
        )

        col1.metric(
            "Total Invoices",
            total
        )

        col2.metric(
            "✅ Auto-Passed",
            len(clean_results)
        )

        col3.metric(
            "⚠️ Exceptions",
            len(exception_results)
        )

        col4.metric(
            "🤔 Human Review",
            len(review_results)
        )

        st.divider()

        # ====================================================
        # RESULT HELPERS
        # ====================================================

        def build_table(
            result_list
        ):

            rows = []

            for result in result_list:

                reason_text = "; ".join(
                    reason.get(
                        "message",
                        ""
                    )
                    for reason in result.get(
                        "reasons",
                        []
                    )
                )

                matched_id = ""

                for reason in result.get(
                    "reasons",
                    []
                ):

                    if reason.get(
                        "matched_invoice_id"
                    ):

                        matched_id = (
                            reason[
                                "matched_invoice_id"
                            ]
                        )

                        break

                rows.append({
                    "Invoice ID": (
                        result.get(
                            "invoice_id"
                        )
                    ),
                    "Status": (
                        result.get(
                            "status"
                        )
                    ),
                    "Rules": ", ".join(
                        result.get(
                            "rule_ids",
                            []
                        )
                    ),
                    "Reason": reason_text,
                    "Matched Invoice": (
                        matched_id
                    ),
                })

            return pd.DataFrame(
                rows
            )

        # ====================================================
        # TABS
        # ====================================================

        (
            tab_pass,
            tab_exceptions,
            tab_review
        ) = st.tabs([
            f"✅ Auto-Passed ({len(clean_results)})",
            f"⚠️ Exceptions ({len(exception_results)})",
            f"🤔 Human Review ({len(review_results)})",
        ])

        # ====================================================
        # AUTO PASS
        # ====================================================

        with tab_pass:

            if clean_results:

                st.dataframe(
                    build_table(
                        clean_results
                    ),
                    use_container_width=True
                )

            else:

                st.info(
                    "No invoices were auto-passed."
                )

        # ====================================================
        # EXCEPTIONS
        # ====================================================

        with tab_exceptions:

            if exception_results:

                st.dataframe(
                    build_table(
                        exception_results
                    ),
                    use_container_width=True
                )

                st.divider()

                for result in exception_results:

                    with st.expander(
                        f"{result.get('invoice_id')} — EXCEPTION"
                    ):

                        st.write(
                            "**Rules triggered:** "
                            + ", ".join(
                                result.get(
                                    "rule_ids",
                                    []
                                )
                            )
                        )

                        for reason in result.get(
                            "reasons",
                            []
                        ):

                            st.write(
                                f"**{reason.get('rule')}**: "
                                f"{reason.get('message')}"
                            )

                            st.write(
                                f"Actual: "
                                f"{reason.get('actual_value')}"
                            )

                            st.write(
                                f"Expected: "
                                f"{reason.get('expected_value')}"
                            )

            else:

                st.success(
                    "No deterministic exceptions found."
                )

        # ====================================================
        # HUMAN REVIEW
        # ====================================================

        with tab_review:

            if review_results:

                st.dataframe(
                    build_table(
                        review_results
                    ),
                    use_container_width=True
                )

                st.divider()

                for result in review_results:

                    with st.expander(
                        f"{result.get('invoice_id')} — HUMAN REVIEW"
                    ):

                        for reason in result.get(
                            "reasons",
                            []
                        ):

                            st.write(
                                f"**{reason.get('rule')}**: "
                                f"{reason.get('message')}"
                            )

                            if reason.get(
                                "matched_invoice_id"
                            ):

                                st.write(
                                    "Matched Invoice: "
                                    + str(
                                        reason[
                                            "matched_invoice_id"
                                        ]
                                    )
                                )

            else:

                st.info(
                    "No invoices currently require human review."
                )

        # ====================================================
        # EXPORT RESULTS
        # ====================================================

        st.divider()

        export_rows = []

        for result in results:

            export_rows.append({
                "invoice_id": result.get(
                    "invoice_id"
                ),
                "status": result.get(
                    "status"
                ),
                "human_review_required": result.get(
                    "human_review_required",
                    False
                ),
                "rule_ids": ", ".join(
                    result.get(
                        "rule_ids",
                        []
                    )
                ),
                "reasons": " | ".join(
                    reason.get(
                        "message",
                        ""
                    )
                    for reason in result.get(
                        "reasons",
                        []
                    )
                ),
            })

        export_df = pd.DataFrame(
            export_rows
        )

        csv_data = export_df.to_csv(
            index=False
        )

        st.download_button(
            "⬇️ Download Results CSV",
            data=csv_data,
            file_name="finsight_results.csv",
            mime="text/csv",
        )