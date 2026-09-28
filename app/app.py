import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st
from src.config import REQUIRED_COLUMNS, CATEGORY_LIMITS
from src.rule_engine import process_invoices, summarize_results
from src.ai import ask_gemini, explain_invoice
from src.persistence import save_audit_event, save_review_action, save_decision

st.set_page_config(page_title="FinSight — AI AP Assistant", page_icon="🧾", layout="wide")
st.markdown("""
<style>
.block-container{max-width:1350px;padding-top:1.6rem}
[data-testid="stMetric"]{padding:12px;border-radius:14px}
.small{opacity:.72;font-size:.88rem}
</style>
""", unsafe_allow_html=True)

for key, default in {
    "results": [], "df": None, "chat": [], "reviews": {}, "audit": [], "analyzed": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.title("🧾 FinSight")
st.caption("AI Accounts-Payable Exception Assistant • deterministic controls + evidence-grounded AI")

with st.sidebar:
    st.header("1. Invoice data")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if st.button("Load included sample", use_container_width=True):
        sample = ROOT / "data" / "invoices.csv"
        st.session_state.df = pd.read_csv(sample)
        st.session_state.results = []
        st.session_state.analyzed = False
        st.session_state.chat = []
        st.success("Sample loaded.")
    st.divider()
    st.subheader("Configured limits")
    for category, limit in CATEGORY_LIMITS.items():
        st.write(f"**{category}** — ₹{limit:,.0f}")
    st.divider()
    st.caption("The rule engine is the source of truth. AI explains trusted results and cannot override them.")

if uploaded is not None:
    try:
        df = pd.read_csv(uploaded)
        st.session_state.df = df
        st.session_state.results = []
        st.session_state.analyzed = False
        st.session_state.chat = []
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}")
        st.stop()

df = st.session_state.df
if df is None:
    st.info("Upload a CSV or load the included sample to begin.")
    st.markdown("**Required columns:** " + ", ".join(REQUIRED_COLUMNS))
    st.stop()
if df.empty:
    st.error("The CSV contains no invoice rows.")
    st.stop()

with st.expander("Preview uploaded data", expanded=not st.session_state.analyzed):
    st.dataframe(df.head(100), use_container_width=True, height=280)

if st.button("🔍 Analyze invoices", type="primary", use_container_width=True):
    try:
        results = process_invoices(df)
        st.session_state.results = results
        st.session_state.analyzed = True
        st.session_state.chat = []
        st.session_state.audit = []
        for r in results:
            event = {
                "timestamp": pd.Timestamp.now().isoformat(),
                "event": "DECISION",
                "invoice_id": str(r["invoice_id"]),
                "message": f"{r['status']} / {r.get('route')} / confidence {r.get('confidence', 0):.0%}",
            }
            st.session_state.audit.append(event)
            save_decision(r)
        st.success(f"Analysis complete — {len(results)} invoice(s) processed.")
    except Exception as exc:
        st.error(str(exc))
        st.stop()

results = st.session_state.results
if not results:
    st.warning("Click **Analyze invoices** to run the checker.")
    st.stop()

summary = summarize_results(results)
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Invoices", summary["total"])
m2.metric("Auto-passed", summary["clean"])
m3.metric("Exceptions", summary["exceptions"])
m4.metric("Human review", summary["review_required"])
avg_conf = sum(r.get("confidence", 0) for r in results) / max(len(results), 1)
m5.metric("Avg. confidence", f"{avg_conf:.0%}")

rows = []
for r in results:
    rows.append({
        "invoice_id": r["invoice_id"],
        "status": r["status"],
        "route": r.get("route", "HUMAN_REVIEW" if r["human_review_required"] else "AUTO_PASS"),
        "confidence": r.get("confidence", 0),
        "rules": ", ".join(r["rule_ids"]) or "None",
    })
display_df = pd.DataFrame(rows)

st.subheader("Control center")
f1, f2, f3 = st.columns([1, 1, 2])
with f1:
    status_filter = st.selectbox("Status", ["ALL", "CLEAN", "EXCEPTION"])
with f2:
    route_filter = st.selectbox("Route", ["ALL", "AUTO_PASS", "HUMAN_REVIEW", "EXCEPTION"])
with f3:
    search = st.text_input("Search invoice ID / rule", placeholder="e.g. INV003 or DUPLICATE")
filtered = display_df.copy()
if status_filter != "ALL":
    filtered = filtered[filtered["status"] == status_filter]
if route_filter != "ALL":
    filtered = filtered[filtered["route"] == route_filter]
if search:
    mask = filtered.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
    filtered = filtered[mask]

st.dataframe(filtered, use_container_width=True, hide_index=True)

tab_pass, tab_exc, tab_review, tab_chat, tab_evidence, tab_audit = st.tabs([
    "✅ Auto-pass", "⚠️ Exceptions", "👤 Human Review", "🤖 FinSight AI", "🔎 Evidence", "📜 Audit & Export"
])

by_id = {str(r["invoice_id"]): r for r in results}

with tab_pass:
    passed = [r for r in results if r["status"] == "CLEAN"]
    st.success(f"{len(passed)} invoice(s) passed all deterministic checks.")
    if passed:
        st.dataframe(pd.DataFrame([{
            "invoice_id": r["invoice_id"], "route": r.get("route"), "confidence": f"{r.get('confidence',0):.0%}",
            "vendor": r["evidence"].get("vendor"), "amount": r["evidence"].get("amount"), "category": r["evidence"].get("category")
        } for r in passed]), use_container_width=True, hide_index=True)

with tab_exc:
    exceptions = [r for r in results if r["status"] == "EXCEPTION"]
    if not exceptions:
        st.success("No deterministic exceptions were found.")
    for r in exceptions:
        with st.container(border=True):
            st.markdown(f"### {r['invoice_id']} • {r.get('route')} • {r.get('confidence',0):.0%} confidence")
            st.write(explain_invoice(r))
            for reason in r["reasons"]:
                st.write(f"**{reason['rule']}** — {reason['message']}")
                st.caption(f"Actual: {reason.get('actual_value')} · Expected: {reason.get('expected_value')}")
                if reason.get("matched_invoice_id"):
                    st.caption(f"Matched invoice: {reason['matched_invoice_id']}")

with tab_review:
    review_items = [r for r in results if r["human_review_required"]]
    st.info(f"{len(review_items)} invoice(s) require human confirmation.")
    for r in review_items:
        iid = str(r["invoice_id"])
        current = st.session_state.reviews.get(iid, {})
        with st.container(border=True):
            st.markdown(f"### {iid} • {r.get('confidence',0):.0%} confidence")
            st.write(explain_invoice(r))
            for reason in r["reasons"]:
                st.write(f"**{reason['rule']}** — {reason['message']}")
            comment = st.text_input("Reviewer comment", value=current.get("comment", ""), key=f"comment_{iid}")
            c1, c2, c3 = st.columns([1, 1, 3])
            with c1:
                if st.button("Approve", key=f"approve_{iid}"):
                    st.session_state.reviews[iid] = {"action": "APPROVED", "comment": comment, "timestamp": pd.Timestamp.now().isoformat()}
                    st.session_state.audit.append({"timestamp": pd.Timestamp.now().isoformat(), "event": "REVIEW", "invoice_id": iid, "message": f"APPROVED: {comment}"})
                    save_review_action(iid, "APPROVED", comment)
                    st.rerun()
            with c2:
                if st.button("Reject", key=f"reject_{iid}"):
                    st.session_state.reviews[iid] = {"action": "REJECTED", "comment": comment, "timestamp": pd.Timestamp.now().isoformat()}
                    st.session_state.audit.append({"timestamp": pd.Timestamp.now().isoformat(), "event": "REVIEW", "invoice_id": iid, "message": f"REJECTED: {comment}"})
                    save_review_action(iid, "REJECTED", comment)
                    st.rerun()
            with c3:
                if current:
                    st.caption(f"Current action: **{current['action']}** at {current['timestamp']}")

with tab_chat:
    st.subheader("Ask FinSight anything about this analysis")
    st.caption("Deterministic questions are answered directly; Gemini handles broader language using trusted evidence only.")
    for role, msg in st.session_state.chat:
        with st.chat_message(role):
            st.write(msg)
    question = st.chat_input("Try: Why is INV003 in human review? / Summarize this batch")
    if question:
        st.session_state.chat.append(("user", question))
        answer, mode = ask_gemini(question, results, st.session_state.chat)
        st.session_state.chat.append(("assistant", answer))
        st.session_state.audit.append({
            "timestamp": pd.Timestamp.now().isoformat(), "event": "AI_QUERY", "invoice_id": "", "message": f"{mode}: {question}"
        })
        save_audit_event("AI_QUERY", "", f"{mode}: {question}")
        st.rerun()

with tab_evidence:
    options = [str(r["invoice_id"]) for r in results]
    selected = st.selectbox("Invoice", options)
    r = by_id[selected]
    st.markdown(f"### {selected}")
    st.write(explain_invoice(r))
    st.write("**Evidence**")
    st.json(r["evidence"])
    st.write("**Rule results**")
    st.json(r["reasons"])
    st.write("**Full trusted result**")
    st.json(r)

with tab_audit:
    audit_df = pd.DataFrame(st.session_state.audit)
    if audit_df.empty:
        st.info("No audit events yet.")
    else:
        st.dataframe(audit_df, use_container_width=True, hide_index=True)
    export = [{
        "invoice_id": r["invoice_id"], "status": r["status"], "route": r.get("route"),
        "confidence": r.get("confidence"), "human_review_required": r["human_review_required"],
        "rule_ids": ", ".join(r["rule_ids"]), "reasons": " | ".join(x["message"] for x in r["reasons"]),
    } for r in results]
    st.download_button("⬇️ Download results CSV", pd.DataFrame(export).to_csv(index=False), "finsight_results.csv", "text/csv")
    st.download_button("⬇️ Download audit JSON", json.dumps(st.session_state.audit, indent=2, default=str), "finsight_audit.json", "application/json")

st.divider()
st.caption("FinSight • 20-day SIH prototype • deterministic source of truth • evidence-grounded AI • human-in-the-loop")
