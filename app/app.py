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
from src.ai import ask_gemini, explain_invoice, test_gemini_connection
from src.persistence import (
    save_audit_event,
    save_review_action,
    save_decision,
    test_supabase_connection,
)

st.set_page_config(
    page_title="FinSight | Invoice Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
  --ink:#172033; --muted:#6b7589; --paper:#f7f8fc; --card:#fff;
  --line:#e7eaf1; --blue:#3157e8; --blue2:#5575ee; --teal:#0f9f9a;
  --amber:#e49a28; --red:#d95b61; --shadow:0 18px 50px rgba(31,44,79,.08);
}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;color:var(--ink)}
.stApp{background:
 radial-gradient(circle at 8% 0%,rgba(49,87,232,.08),transparent 28%),
 radial-gradient(circle at 96% 10%,rgba(15,159,154,.08),transparent 25%),var(--paper)}
.block-container{max-width:1480px;padding-top:1.6rem;padding-bottom:4rem}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.04em}
[data-testid="stSidebar"]{background:rgba(255,255,255,.9);border-right:1px solid var(--line)}
div.stButton>button,div.stDownloadButton>button{border-radius:12px;border:1px solid var(--line);min-height:42px;font-weight:600;transition:.18s ease}
div.stButton>button:hover,div.stDownloadButton>button:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(31,44,79,.1)}
button[kind="primary"]{background:linear-gradient(135deg,var(--blue),var(--blue2))!important;color:#fff!important;border:0!important;box-shadow:0 10px 24px rgba(49,87,232,.22)}
[data-testid="stMetric"]{background:rgba(255,255,255,.88);border:1px solid var(--line);border-radius:18px;padding:16px 18px;box-shadow:0 10px 30px rgba(31,44,79,.045);animation:rise .45s ease both}
[data-testid="stMetricValue"]{font-family:'Space Grotesk',sans-serif}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:15px;overflow:hidden}
[data-testid="stChatMessage"]{border:1px solid var(--line);border-radius:18px;margin-bottom:10px;animation:slide .3s ease both}
.stTabs [data-baseweb="tab-list"]{gap:5px;background:rgba(255,255,255,.72);padding:5px;border:1px solid var(--line);border-radius:14px}
.stTabs [data-baseweb="tab"]{border-radius:9px;padding:8px 13px}
.stTabs [aria-selected="true"]{background:#eef2ff;color:var(--blue)}
.fs-hero{position:relative;overflow:hidden;padding:32px 36px;border-radius:26px;background:linear-gradient(110deg,#fff,rgba(245,248,255,.92));border:1px solid var(--line);box-shadow:var(--shadow);animation:rise .6s ease both}
.fs-hero:after{content:"";position:absolute;width:220px;height:220px;right:-70px;top:-110px;border:32px solid rgba(49,87,232,.07);border-radius:50%;animation:spin 12s linear infinite}
.kicker{color:var(--blue);font-size:.76rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase}
.hero-title{font-family:'Space Grotesk';font-size:clamp(2rem,4vw,3.6rem);line-height:.98;letter-spacing:-.065em;margin:8px 0 12px}
.hero-copy{color:var(--muted);max-width:800px;font-size:1.02rem}
.pill{display:inline-block;padding:7px 11px;margin:8px 5px 0 0;border:1px solid var(--line);border-radius:999px;background:#fff;font-size:.78rem;font-weight:600}
.card{background:rgba(255,255,255,.9);border:1px solid var(--line);border-radius:20px;padding:20px;box-shadow:0 10px 34px rgba(31,44,79,.055);animation:rise .45s ease both}
.section{font-family:'Space Grotesk';font-weight:700;font-size:1.1rem;margin:25px 0 10px}
.muted{color:var(--muted);font-size:.84rem}
.result-banner{border-radius:20px;padding:18px 20px;border:1px solid var(--line);background:#fff;box-shadow:0 10px 30px rgba(31,44,79,.06);animation:rise .4s ease both}
.status-clean{color:#087c6e;background:#e9faf7}
.status-exception{color:#a3454d;background:#fff0f1}
.status-review{color:#95651b;background:#fff7e8}
.status-chip{display:inline-block;padding:6px 10px;border-radius:999px;font-size:.75rem;font-weight:700}
.action-row{border:1px solid var(--line);border-radius:16px;padding:14px;background:rgba(255,255,255,.7)}
@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
@keyframes slide{from{opacity:0;transform:translateX(8px)}to{opacity:1;transform:none}}
@keyframes spin{to{transform:rotate(360deg)}}
button,a,input[type="file"],[role="button"]{cursor:pointer}
button:focus-visible,input:focus-visible,textarea:focus-visible{outline:3px solid rgba(49,87,232,.22)!important;outline-offset:2px}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style>
""",
    unsafe_allow_html=True,
)

defaults = {
    "df": None, "results": [], "analyzed": False, "chat": [], "reviews": {},
    "audit": [], "gemini_health": None, "supabase_health": None,
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

with st.sidebar:
    st.markdown("## ✦ FinSight")
    st.caption("Invoice intelligence workspace")
    st.divider()
    uploaded = st.file_uploader("Upload invoice CSV", type=["csv"])
    if st.button("Use sample invoices", use_container_width=True):
        st.session_state.df = pd.read_csv(ROOT / "data" / "invoices.csv")
        st.session_state.results = []
        st.session_state.analyzed = False
        st.session_state.chat = []
        st.toast("Sample invoices loaded", icon="✦")
    st.divider()
    st.markdown("**Workspace**")
    view = st.radio(
        "Navigate",
        ["Command Center","AI Copilot","Review Queue","Evidence","Audit & Export"],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown("**Connections**")
    if st.button("Check connections", use_container_width=True):
        st.session_state.gemini_health = test_gemini_connection()
        st.session_state.supabase_health = test_supabase_connection()
        st.toast("Connection checks completed", icon="🔗")
    gh, sh = st.session_state.gemini_health, st.session_state.supabase_health
    st.caption("🟢 Gemini connected" if gh and gh[0] else "⚪ Gemini not checked / unavailable")
    st.caption("🟢 Supabase connected" if sh and sh[0] else "⚪ Supabase not checked / unavailable")
    st.divider()
    st.markdown("**Control limits**")
    for category, limit in CATEGORY_LIMITS.items():
        st.caption(f"{category} · ₹{limit:,.0f}")

if uploaded is not None:
    try:
        st.session_state.df = pd.read_csv(uploaded)
        st.session_state.results = []
        st.session_state.analyzed = False
        st.session_state.chat = []
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}")
        st.stop()

df = st.session_state.df

st.markdown(
    """
<div class="fs-hero">
  <div class="kicker">Accounts payable · intelligence layer</div>
  <div class="hero-title">From invoice upload<br>to a decision you can explain.</div>
  <div class="hero-copy">Run deterministic controls, inspect the evidence behind every result, send uncertain cases to human review, and use the AI copilot for grounded explanations.</div>
  <span class="pill">✦ Evidence first</span>
  <span class="pill">◉ Human review</span>
  <span class="pill">↗ Audit ready</span>
  <span class="pill">⌁ AI copilot</span>
</div>
""",
    unsafe_allow_html=True,
)

if df is None:
    st.markdown('<div class="section">Start here</div>', unsafe_allow_html=True)
    a,b,c = st.columns(3)
    for col,title,copy in [
        (a,"01 · Upload","Add your invoice CSV from the left panel."),
        (b,"02 · Analyze","FinSight checks fields, limits, dates and duplicates."),
        (c,"03 · Review","See every decision and why it happened."),
    ]:
        with col:
            st.markdown(f'<div class="card"><b>{title}</b><br><span class="muted">{copy}</span></div>',unsafe_allow_html=True)
    st.info("Upload a CSV or use the sample dataset to begin.")
    st.stop()

if df.empty:
    st.error("The CSV contains no invoice rows.")
    st.stop()

# Analysis workspace is always visible before the navigation views.
st.markdown('<div class="section">Analysis workspace</div>', unsafe_allow_html=True)
left,right = st.columns([4,1])
with left:
    st.markdown(
        f'<div class="muted"><b>{len(df):,}</b> invoice row(s) loaded · required: {", ".join(REQUIRED_COLUMNS)}</div>',
        unsafe_allow_html=True,
    )
with right:
    analyze = st.button("Analyze invoices", type="primary", use_container_width=True)

if analyze:
    try:
        with st.spinner("Checking invoices and building evidence…"):
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
                    "message": f"{r['status']} / {r.get('route')} / confidence {r.get('confidence',0):.0%}",
                }
                st.session_state.audit.append(event)
                save_decision(r)
        st.toast(f"{len(results)} invoices analyzed", icon="✅")
        st.rerun()
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")
        st.stop()

if not st.session_state.analyzed:
    with st.expander("Preview source data", expanded=True):
        st.dataframe(df.head(100), use_container_width=True, hide_index=True)
    st.info("Click Analyze invoices. The complete result appears directly below this section.")
    st.stop()

results = st.session_state.results
if not results:
    st.warning("Analysis returned no results.")
    st.stop()

summary = summarize_results(results)
avg_conf = sum(float(r.get("confidence",0)) for r in results)/max(len(results),1)

# ---------------------------------------------------------------------------
# ALWAYS-VISIBLE ANALYSIS RESULTS
# ---------------------------------------------------------------------------
st.markdown('<div class="section">Analysis results</div>', unsafe_allow_html=True)
m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("Invoices", summary["total"])
m2.metric("Auto-pass", summary["clean"])
m3.metric("Exceptions", summary["exceptions"])
m4.metric("Human review", summary["review_required"])
m5.metric("Avg confidence", f"{avg_conf:.0%}")

table_rows = []
for r in results:
    route = r.get("route") or ("HUMAN_REVIEW" if r.get("human_review_required") else "AUTO_PASS")
    table_rows.append({
        "Invoice": str(r.get("invoice_id","")),
        "Status": str(r.get("status","")),
        "Route": route,
        "Confidence": float(r.get("confidence",0)),
        "Rules": ", ".join(r.get("rule_ids",[])) or "None",
    })
result_df = pd.DataFrame(table_rows)

st.dataframe(
    result_df,
    use_container_width=True,
    hide_index=True,
    column_config={"Confidence": st.column_config.ProgressColumn("Confidence",min_value=0,max_value=1,format="%.0f%%")},
)

# Human-readable result cards for the first several invoices.
st.markdown('<div class="section">What happened?</div>', unsafe_allow_html=True)
for r in results[:8]:
    status = str(r.get("status","UNKNOWN"))
    route = r.get("route") or ("HUMAN_REVIEW" if r.get("human_review_required") else "AUTO_PASS")
    cls = "status-clean" if status == "CLEAN" else ("status-review" if r.get("human_review_required") else "status-exception")
    reasons = r.get("reasons",[])
    reason_text = reasons[0].get("message","No rule issues detected.") if reasons else "No rule issues detected."
    st.markdown(
        f'<div class="result-banner"><b>{r.get("invoice_id","Invoice")}</b> '
        f'<span class="status-chip {cls}">{status}</span> '
        f'<span class="status-chip">{route}</span> '
        f'<span class="status-chip">{float(r.get("confidence",0)):.0%} confidence</span><br>'
        f'<span class="muted">{reason_text}</span></div>',
        unsafe_allow_html=True,
    )
if len(results) > 8:
    st.caption(f"Showing 8 of {len(results)} invoice explanations. Use Evidence for any invoice.")

# ---------------------------------------------------------------------------
# Secondary workspace
# ---------------------------------------------------------------------------
st.markdown('<div class="section">Workspace</div>', unsafe_allow_html=True)

if view == "Command Center":
    f1,f2,f3 = st.columns([1,1,2])
    with f1: status_filter = st.selectbox("Status filter",["ALL","CLEAN","EXCEPTION"])
    with f2: route_filter = st.selectbox("Route filter",["ALL","AUTO_PASS","HUMAN_REVIEW","EXCEPTION"])
    with f3: search = st.text_input("Search results",placeholder="Invoice ID, rule or vendor")
    filtered = result_df.copy()
    if status_filter != "ALL": filtered = filtered[filtered["Status"] == status_filter]
    if route_filter != "ALL": filtered = filtered[filtered["Route"] == route_filter]
    if search:
        filtered = filtered[filtered.astype(str).apply(lambda x:x.str.contains(search,case=False,na=False)).any(axis=1)]
    st.dataframe(filtered,use_container_width=True,hide_index=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card"><b>Decision flow</b><br><span class="muted">CSV → deterministic rules → evidence → route → explanation → human decision when required.</span></div>',unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card"><b>Source of truth</b><br><span class="muted">The rule engine makes the decision. AI is used to explain trusted results, not override them.</span></div>',unsafe_allow_html=True)

elif view == "AI Copilot":
    st.markdown('<div class="card"><h3>✦ FinSight Copilot</h3><span class="muted">Ask about this analyzed batch. Answers are grounded in the current results.</span></div>',unsafe_allow_html=True)
    q1,q2,q3 = st.columns(3)
    suggestions = ["Summarize this batch","Which invoices need human review?","Explain the exceptions"]
    for col,suggestion in zip([q1,q2,q3],suggestions):
        with col:
            if st.button(suggestion,use_container_width=True):
                st.session_state.chat.append(("user",suggestion))
                answer,mode = ask_gemini(suggestion,results,st.session_state.chat)
                st.session_state.chat.append(("assistant",answer))
                st.session_state.audit.append({"timestamp":pd.Timestamp.now().isoformat(),"event":"AI_QUERY","invoice_id":"","message":f"{mode}: {suggestion}"})
                save_audit_event("AI_QUERY","",f"{mode}: {suggestion}")
                st.rerun()
    for role,msg in st.session_state.chat:
        with st.chat_message(role): st.write(msg)
    question = st.chat_input("Ask about an invoice, exception, rule or decision…")
    if question:
        st.session_state.chat.append(("user",question))
        answer,mode = ask_gemini(question,results,st.session_state.chat)
        st.session_state.chat.append(("assistant",answer))
        st.session_state.audit.append({"timestamp":pd.Timestamp.now().isoformat(),"event":"AI_QUERY","invoice_id":"","message":f"{mode}: {question}"})
        save_audit_event("AI_QUERY","",f"{mode}: {question}")
        st.rerun()

elif view == "Review Queue":
    review_items = [r for r in results if r.get("human_review_required")]
    st.markdown(f'<div class="card"><b>{len(review_items)} invoice(s)</b> require human review.</div>',unsafe_allow_html=True)
    for r in review_items:
        iid=str(r["invoice_id"]); current=st.session_state.reviews.get(iid,{})
        with st.container(border=True):
            st.markdown(f"### {iid} · {float(r.get('confidence',0)):.0%} confidence")
            st.write(explain_invoice(r))
            for reason in r.get("reasons",[]): st.markdown(f"**{reason['rule']}** — {reason['message']}")
            comment=st.text_input("Reviewer note",value=current.get("comment",""),key=f"comment_{iid}")
            a,b=st.columns(2)
            with a:
                if st.button("Approve",key=f"approve_{iid}",use_container_width=True):
                    st.session_state.reviews[iid]={"action":"APPROVED","comment":comment,"timestamp":pd.Timestamp.now().isoformat()}
                    save_review_action(iid,"APPROVED",comment); st.rerun()
            with b:
                if st.button("Reject",key=f"reject_{iid}",use_container_width=True):
                    st.session_state.reviews[iid]={"action":"REJECTED","comment":comment,"timestamp":pd.Timestamp.now().isoformat()}
                    save_review_action(iid,"REJECTED",comment); st.rerun()
    if not review_items: st.success("No invoices currently require human review.")

elif view == "Evidence":
    by_id={str(r["invoice_id"]):r for r in results}
    selected=st.selectbox("Select invoice",list(by_id))
    r=by_id[selected]
    st.markdown(f'<div class="card"><h3>{selected}</h3><span class="muted">{r.get("status")} · {r.get("route")} · {float(r.get("confidence",0)):.0%} confidence</span><br><br>{explain_invoice(r)}</div>',unsafe_allow_html=True)
    st.markdown("#### Evidence"); st.json(r.get("evidence",{}))
    st.markdown("#### Rule results"); st.json(r.get("reasons",[]))

else:
    st.markdown('<div class="card"><h3>Audit trail</h3><span class="muted">Decision and AI events recorded during this session.</span></div>',unsafe_allow_html=True)
    audit_df=pd.DataFrame(st.session_state.audit)
    if audit_df.empty: st.info("No audit events yet.")
    else: st.dataframe(audit_df,use_container_width=True,hide_index=True)
    export=[{"invoice_id":r["invoice_id"],"status":r["status"],"route":r.get("route"),"confidence":r.get("confidence"),"human_review_required":r["human_review_required"],"rule_ids":", ".join(r.get("rule_ids",[])),"reasons":" | ".join(x["message"] for x in r.get("reasons",[]))} for r in results]
    c1,c2=st.columns(2)
    with c1: st.download_button("Download results CSV",pd.DataFrame(export).to_csv(index=False),"finsight_results.csv","text/csv",use_container_width=True)
    with c2: st.download_button("Download audit JSON",json.dumps(st.session_state.audit,indent=2,default=str),"finsight_audit.json","application/json",use_container_width=True)

st.divider()
st.caption("FinSight · deterministic controls · evidence-grounded AI · human-in-the-loop")
