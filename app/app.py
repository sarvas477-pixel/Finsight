import streamlit as st
import pandas as pd

st.title("AuditMate AI")
st.write("Invoice Exception Assistant")

st.header("Upload your invoice CSV")

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"]
)

if uploaded_file is not None:
    st.success("File uploaded successfully!")

    df = pd.read_csv(uploaded_file)

    st.subheader("Summary")

    st.write("Total invoices:", len(df))

    st.subheader("Invoice Data")
    st.dataframe(df)

else:
    st.info("No file uploaded yet.")