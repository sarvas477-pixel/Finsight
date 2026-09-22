import pandas as pd
import streamlit as st

from src.config import REQUIRED_COLUMNS
from src.invoice_pipeline import process_invoice_dataframe

st.set_page_config(page_title="FinSight Invoice Checker", page_icon="🧾", layout="wide")
st.title("🧾 FinSight Invoice Checker")
st.caption("Upload a CSV to validate invoices, explain exceptions, and route them safely.")

uploaded = st.file_uploader("Upload invoice CSV", type="csv")
if uploaded is None:
    st.info("Upload a CSV with: " + ", ".join(REQUIRED_COLUMNS))
    st.stop()

try:
    df = pd.read_csv(uploaded)
except pd.errors.EmptyDataError:
    st.error("The uploaded CSV is empty.")
    st.stop()
except (pd.errors.ParserError, UnicodeDecodeError) as error:
    st.error(f"Could not read the CSV: {error}")
    st.stop()

missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.stop()
if df.empty:
    st.warning("The uploaded CSV contains no invoice rows.")
    st.stop()

st.success(f"Loaded {len(df)} invoice(s).")
with st.expander("Preview uploaded data"):
    st.dataframe(df, use_container_width=True)

if st.button("Check invoices", type="primary"):
    try:
        results = process_invoice_dataframe(df)
    except (TypeError, ValueError) as error:
        st.error(str(error))
        st.stop()

    auto_pass = [r for r in results if r["route"] == "AUTO_PASS"]
    exceptions = [r for r in results if r["route"] == "EXCEPTION"]
    review = [r for r in results if r["route"] == "HUMAN_REVIEW"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", len(results))
    c2.metric("Auto-passed", len(auto_pass))
    c3.metric("Exceptions", len(exceptions))
    c4.metric("Human review", len(review))

    rows = []
    for result in results:
        rows.append({
            "Invoice ID": result.get("invoice_id"),
            "Route": result.get("route"),
            "Confidence": result.get("confidence"),
            "Rules": ", ".join(result.get("rule_ids", [])),
            "Explanation": result.get("explanation", ""),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    st.download_button(
        "Download results CSV",
        pd.DataFrame(rows).to_csv(index=False),
        "finsight_results.csv",
        "text/csv",
    )
