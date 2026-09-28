import sys, io, json, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st
from src.config import REQUIRED_COLUMNS, CATEGORY_LIMITS
from src.rule_engine import process_invoices, summarize_results
from src.ai import ask_gemini, explain_invoice
from src.persistence import save_audit_event, save_review_action

st.set_page_config(page_title="FinSight — AI AP Assistant", page_icon="🧾", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1250px;padding-top:2rem}
[data-testid="stMetric"]{background:#0f1b22;border:1px solid #20353e;padding:12px;border-radius:14px}
.chatbox{padding:14px 18px;border:1px solid #243b44;border-radius:16px;background:#0d181e;margin:8px 0}
.small{color:#91a9af;font-size:.88rem}
</style>
""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results = []
if "df" not in st.session_state: st.session_state.df = None
if "chat" not in st.session_state: st.session_state.chat = []
if "reviews" not in st.session_state: st.session_state.reviews = {}
if "audit" not in st.session_state: st.session_state.audit = []

st.title("🧾 FinSight")
st.caption("AI Accounts-Payable Exception Assistant")
st.write("Upload invoice data, let FinSight validate it deterministically, then ask the AI assistant about the evidence.")

with st.sidebar:
    st.header("Invoice data")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if st.button("Load included sample"):
        sample = ROOT / "data" / "invoices.csv"
        st.session_state.df = pd.read_csv(sample)
        st.session_state.results = process_invoices(st.session_state.df)
        st.session_state.chat = []
        st.success("Sample loaded.")
    st.divider()
    st.subheader("Configured limits")
    for k,v in CATEGORY_LIMITS.items():
        st.write(f"**{k}** — ₹{v:,.0f}")
    st.caption("Deterministic rules are the source of truth. Gemini explains them; it does not override them.")

if uploaded is not None:
    try:
        df = pd.read_csv(uploaded)
        st.session_state.df = df
        st.session_state.results = []
        st.session_state.chat = []
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        st.stop()

df = st.session_state.df
if df is None:
    st.info("Start by uploading an invoice CSV or loading the included sample.")
    st.markdown("**Required columns:** " + ", ".join(REQUIRED_COLUMNS))
    st.stop()

if df.empty:
    st.error("The CSV contains no invoice rows.")
    st.stop()

if st.button("🔍 Analyze invoices", type="primary", use_container_width=True):
    try:
        st.session_state.results = process_invoices(df)
        st.session_state.chat = []
        st.session_state.audit = []
        for r in st.session_state.results:
            st.session_state.audit.append({
                "timestamp": pd.Timestamp.now().isoformat(),
                "event": "DECISION",
                "invoice_id": r["invoice_id"],
                "message": f"{r['status']} / {'HUMAN_REVIEW' if r['human_review_required'] else 'AUTO'}"
            })
        st.success("Analysis complete.")
    except Exception as e:
        st.error(str(e))
        st.stop()

results = st.session_state.results
if not results:
    st.warning("Click **Analyze invoices** to run the checker.")
    with st.expander("Preview uploaded data"):
        st.dataframe(df, use_container_width=True)
    st.stop()

summary = summarize_results(results)
m1,m2,m3,m4 = st.columns(4)
m1.metric("Invoices", summary["total"])
m2.metric("Auto-passed", summary["clean"])
m3.metric("Exceptions", summary["exceptions"])
m4.metric("Human review", summary["review_required"])

tab_chat, tab_review, tab_evidence, tab_audit = st.tabs(["🤖 FinSight AI", "👤 Human Review", "🔎 Evidence", "📜 Audit & Export"])

with tab_chat:
    st.subheader("Ask FinSight")
    st.caption("Answers are grounded in the current deterministic analysis.")
    for role, msg in st.session_state.chat:
        with st.chat_message(role):
            st.write(msg)
    question = st.chat_input("Ask: Why is INV003 in human review?")
    if question:
        st.session_state.chat.append(("user", question))
        answer, mode = ask_gemini(question, results)
        st.session_state.chat.append(("assistant", answer))
        st.session_state.audit.append({
            "timestamp": pd.Timestamp.now().isoformat(),
            "event": "AI_QUERY",
            "invoice_id": "",
            "message": f"{mode}: {question}"
        })
        st.rerun()

with tab_review:
    review_items = [r for r in results if r["human_review_required"]]
    if not review_items:
        st.success("No invoices require human review.")
    for r in review_items:
        iid = str(r["invoice_id"])
        with st.container(border=True):
            st.markdown(f"### {iid}")
            st.write(explain_invoice(r))
            for reason in r["reasons"]:
                st.write(f"**{reason['rule']}** — {reason['message']}")
                st.caption(f"Actual: {reason.get('actual_value')} · Expected: {reason.get('expected_value')}")
                if reason.get("matched_invoice_id"):
                    st.caption(f"Matched invoice: {reason['matched_invoice_id']}")
            current = st.session_state.reviews.get(iid, {})
            c1,c2,c3 = st.columns([1,1,3])
            with c1:
                if st.button("Approve", key=f"approve_{iid}"):
                    st.session_state.reviews[iid] = {"action":"APPROVED","comment":current.get("comment","")}
                    st.session_state.audit.append({"timestamp":pd.Timestamp.now().isoformat(),"event":"REVIEW","invoice_id":iid,"message":"APPROVED"})
                    save_review_action(iid, "APPROVED", current.get("comment",""))
                    st.rerun()
            with c2:
                if st.button("Reject", key=f"reject_{iid}"):
                    st.session_state.reviews[iid] = {"action":"REJECTED","comment":current.get("comment","")}
                    st.session_state.audit.append({"timestamp":pd.Timestamp.now().isoformat(),"event":"REVIEW","invoice_id":iid,"message":"REJECTED"})
                    save_review_action(iid, "REJECTED", current.get("comment",""))
                    st.rerun()
            with c3:
                comment = st.text_input("Reviewer comment", value=current.get("comment",""), key=f"comment_{iid}")
                if comment != current.get("comment",""):
                    st.session_state.reviews[iid] = {**current, "comment": comment}

with tab_evidence:
    options = [str(r["invoice_id"]) for r in results]
    selected = st.selectbox("Invoice", options)
    r = next(x for x in results if str(x["invoice_id"]) == selected)
    st.markdown(f"### {selected}")
    st.write(explain_invoice(r))
    st.json(r)

with tab_audit:
    audit_df = pd.DataFrame(st.session_state.audit)
    if audit_df.empty:
        st.info("No audit events yet.")
    else:
        st.dataframe(audit_df, use_container_width=True)
    export = []
    for r in results:
        export.append({
            "invoice_id": r["invoice_id"],
            "status": r["status"],
            "human_review_required": r["human_review_required"],
            "rule_ids": ", ".join(r["rule_ids"]),
            "reasons": " | ".join(x["message"] for x in r["reasons"]),
        })
    csv = pd.DataFrame(export).to_csv(index=False)
    st.download_button("⬇️ Download results CSV", csv, "finsight_results.csv", "text/csv")
    audit_json = json.dumps(st.session_state.audit, indent=2, default=str)
    st.download_button("⬇️ Download audit JSON", audit_json, "finsight_audit.json", "application/json")

st.divider()
st.caption("FinSight • deterministic invoice controls + evidence-grounded AI • no login required")
