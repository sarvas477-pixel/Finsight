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
    page_title="FinSight — AP Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# FinSight design system
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
  --ink: #172033;
  --muted: #68738a;
  --paper: #f7f8fc;
  --card: rgba(255,255,255,.88);
  --line: #e7eaf1;
  --blue: #3157e8;
  --blue-soft: #eef2ff;
  --teal: #0f9f9a;
  --teal-soft: #e9faf7;
  --amber: #e49a28;
  --amber-soft: #fff7e8;
  --red: #d95b61;
  --red-soft: #fff0f1;
  --shadow: 0 18px 50px rgba(31, 44, 79, .08);
}

html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif;
  color: var(--ink);
}

.stApp {
  background:
    radial-gradient(circle at 8% 0%, rgba(49,87,232,.08), transparent 28%),
    radial-gradient(circle at 95% 12%, rgba(15,159,154,.08), transparent 25%),
    var(--paper);
}

.block-container {
  max-width: 1440px;
  padding-top: 2rem;
  padding-bottom: 4rem;
}

h1, h2, h3, h4 {
  font-family: 'Space Grotesk', sans-serif !important;
  letter-spacing: -.035em;
}

[data-testid="stSidebar"] {
  background: rgba(255,255,255,.86);
  border-right: 1px solid var(--line);
  backdrop-filter: blur(18px);
}

[data-testid="stSidebar"] > div:first-child {
  padding-top: 1.5rem;
}

div.stButton > button,
div.stDownloadButton > button {
  border-radius: 12px;
  border: 1px solid var(--line);
  min-height: 42px;
  font-weight: 600;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}

div.stButton > button:hover,
div.stDownloadButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(31,44,79,.10);
  border-color: rgba(49,87,232,.35);
}

button[kind="primary"] {
  background: linear-gradient(135deg, #3157e8, #5575ee) !important;
  border: none !important;
  color: white !important;
  box-shadow: 0 10px 24px rgba(49,87,232,.22);
}

button[kind="primary"]:hover {
  box-shadow: 0 14px 30px rgba(49,87,232,.28) !important;
}

[data-testid="stMetric"] {
  background: var(--card);
  border: 1px solid rgba(231,234,241,.9);
  border-radius: 18px;
  padding: 18px 20px;
  box-shadow: 0 10px 30px rgba(31,44,79,.045);
  animation: rise .55s ease both;
}

[data-testid="stMetricValue"] {
  font-family: 'Space Grotesk', sans-serif;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 6px;
  background: rgba(255,255,255,.7);
  padding: 6px;
  border: 1px solid var(--line);
  border-radius: 15px;
}

.stTabs [data-baseweb="tab"] {
  border-radius: 10px;
  padding: 8px 14px;
  transition: all .18s ease;
}

.stTabs [aria-selected="true"] {
  background: var(--blue-soft);
  color: var(--blue);
}

[data-testid="stChatMessage"] {
  border: 1px solid var(--line);
  border-radius: 18px;
  margin-bottom: 12px;
  padding: 4px;
  animation: slideIn .35s ease both;
  box-shadow: 0 8px 24px rgba(31,44,79,.04);
}

[data-testid="stChatInput"] {
  animation: floatIn .4s ease both;
}

.stTextInput input, .stSelectbox, .stFileUploader {
  border-radius: 12px;
}

[data-testid="stDataFrame"] {
  border: 1px solid var(--line);
  border-radius: 15px;
  overflow: hidden;
}

.fs-hero {
  position: relative;
  overflow: hidden;
  padding: 30px 34px;
  border-radius: 26px;
  color: var(--ink);
  background:
    linear-gradient(110deg, rgba(255,255,255,.96), rgba(245,248,255,.90)),
    radial-gradient(circle at 85% 25%, rgba(49,87,232,.12), transparent 32%);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  animation: rise .65s ease both;
}

.fs-hero:after {
  content: "";
  position: absolute;
  width: 230px;
  height: 230px;
  right: -80px;
  top: -100px;
  border-radius: 50%;
  border: 35px solid rgba(49,87,232,.07);
  animation: orbit 9s linear infinite;
}

.fs-kicker {
  color: var(--blue);
  font-size: .78rem;
  font-weight: 700;
  letter-spacing: .13em;
  text-transform: uppercase;
}

.fs-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: clamp(2rem, 4vw, 3.5rem);
  line-height: .98;
  letter-spacing: -.06em;
  margin: 7px 0 13px;
}

.fs-subtitle {
  color: var(--muted);
  max-width: 760px;
  font-size: 1.02rem;
}

.fs-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 11px;
  margin: 5px 5px 0 0;
  border-radius: 999px;
  background: white;
  border: 1px solid var(--line);
  font-size: .78rem;
  font-weight: 600;
  color: #4d5870;
  transition: transform .18s ease;
}

.fs-pill:hover { transform: translateY(-2px); }

.fs-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 10px 34px rgba(31,44,79,.055);
  animation: slideIn .45s ease both;
}

.fs-card:hover {
  box-shadow: 0 16px 42px rgba(31,44,79,.09);
}

.fs-chat-hero {
  text-align: center;
  padding: 22px 20px 8px;
}

.fs-orb {
  width: 58px;
  height: 58px;
  margin: 0 auto 12px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  color: white;
  font-size: 1.5rem;
  background: linear-gradient(135deg, #3157e8, #0f9f9a);
  box-shadow: 0 14px 28px rgba(49,87,232,.22);
  animation: breathe 3.5s ease-in-out infinite;
}

.fs-chat-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.7rem;
  letter-spacing: -.04em;
}

.fs-chat-copy {
  color: var(--muted);
  margin: 5px auto 18px;
  max-width: 620px;
}

.fs-status {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.fs-status-item {
  padding: 7px 10px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid var(--line);
  font-size: .78rem;
}

.fs-status-ok { color: #087c6e; background: var(--teal-soft); }
.fs-status-off { color: #9a6570; background: var(--red-soft); }

.fs-section {
  margin: 22px 0 10px;
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: 1.08rem;
}

.fs-mini {
  color: var(--muted);
  font-size: .82rem;
}

.fs-feature {
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 15px;
  background: rgba(255,255,255,.7);
  transition: transform .18s ease, box-shadow .18s ease;
}

.fs-feature:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(31,44,79,.08);
}

@keyframes rise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes slideIn {
  from { opacity: 0; transform: translateX(10px); }
  to { opacity: 1; transform: translateX(0); }
}
@keyframes floatIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes breathe {
  0%,100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-4px) scale(1.035); }
}
@keyframes orbit {
  to { transform: rotate(360deg); }
}

/* Intentional cursor feedback: pointer targets feel interactive without hiding
   the system cursor, preserving accessibility. */
button, a, input[type="file"], [role="button"] { cursor: pointer; }
button:focus-visible, input:focus-visible, textarea:focus-visible {
  outline: 3px solid rgba(49,87,232,.24) !important;
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
defaults = {
    "results": [],
    "df": None,
    "chat": [],
    "reviews": {},
    "audit": [],
    "analyzed": False,
    "active_view": "Command Center",
    "gemini_health": None,
    "supabase_health": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ✦ FinSight")
    st.caption("AP intelligence workspace")
    st.divider()

    nav = st.radio(
        "Workspace",
        ["Command Center", "AI Copilot", "Review Queue", "Evidence", "Audit & Export"],
        index=["Command Center", "AI Copilot", "Review Queue", "Evidence", "Audit & Export"].index(
            st.session_state.active_view
        ),
        label_visibility="collapsed",
    )
    st.session_state.active_view = nav

    st.divider()
    st.markdown("**Invoice source**")
    uploaded = st.file_uploader("Drop a CSV", type=["csv"], label_visibility="collapsed")
    if st.button("Load sample dataset", use_container_width=True):
        sample = ROOT / "data" / "invoices.csv"
        st.session_state.df = pd.read_csv(sample)
        st.session_state.results = []
        st.session_state.analyzed = False
        st.session_state.chat = []
        st.toast("Sample invoices loaded", icon="✦")

    st.divider()
    st.markdown("**System health**")
    if st.button("Check connections", use_container_width=True):
        st.session_state.gemini_health = test_gemini_connection()
        st.session_state.supabase_health = test_supabase_connection()
        st.toast("Connection checks completed", icon="🔗")

    gh = st.session_state.gemini_health
    sh = st.session_state.supabase_health
    st.markdown(
        f'<div class="fs-status">'
        f'<span class="fs-status-item {"fs-status-ok" if gh and gh[0] else "fs-status-off"}">{"● Gemini connected" if gh and gh[0] else "○ Gemini not checked / unavailable"}</span>'
        f'<span class="fs-status-item {"fs-status-ok" if sh and sh[0] else "fs-status-off"}">{"● Supabase connected" if sh and sh[0] else "○ Supabase not checked / unavailable"}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("**Configured controls**")
    for category, limit in CATEGORY_LIMITS.items():
        st.caption(f"{category}  ·  ₹{limit:,.0f}")

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

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
<div class="fs-hero">
  <div class="fs-kicker">Accounts payable · intelligence layer</div>
  <div class="fs-title">Make every invoice<br>easy to explain.</div>
  <div class="fs-subtitle">
    FinSight combines deterministic invoice controls with an evidence-grounded AI copilot
    and human review workflow. The rules decide; the AI explains.
  </div>
  <div>
    <span class="fs-pill">✦ Evidence first</span>
    <span class="fs-pill">◉ Human in the loop</span>
    <span class="fs-pill">↗ Audit ready</span>
    <span class="fs-pill">⌁ Gemini copilot</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

if df is None:
    st.markdown('<div class="fs-section">Start an analysis</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    with a:
        st.markdown('<div class="fs-feature"><b>01 · Upload</b><br><span class="fs-mini">Drop your invoice CSV using the left panel.</span></div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="fs-feature"><b>02 · Analyze</b><br><span class="fs-mini">Run deterministic checks for fields, limits and duplicates.</span></div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="fs-feature"><b>03 · Ask</b><br><span class="fs-mini">Chat with FinSight about the trusted results.</span></div>', unsafe_allow_html=True)

    st.info("Upload a CSV or load the included sample dataset to open the workspace.")
    st.stop()

if df.empty:
    st.error("The CSV contains no invoice rows.")
    st.stop()

# ---------------------------------------------------------------------------
# Analyze control
# ---------------------------------------------------------------------------
top_a, top_b = st.columns([5, 1])
with top_a:
    st.markdown(
        f'<div class="fs-mini"><b>{len(df):,}</b> source row(s) loaded · required fields: {", ".join(REQUIRED_COLUMNS)}</div>',
        unsafe_allow_html=True,
    )
with top_b:
    if st.button("Analyze", type="primary", use_container_width=True):
        try:
            with st.spinner("FinSight is checking every row…"):
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
            st.toast(f"{len(results)} invoices analyzed", icon="✅")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
            st.stop()

if not st.session_state.analyzed:
    with st.expander("Preview source data", expanded=True):
        st.dataframe(df.head(100), use_container_width=True, height=300)
    st.info("Run **Analyze** to activate the command center and AI copilot.")
    st.stop()

results = st.session_state.results
if not results:
    st.warning("No analysis results are available.")
    st.stop()

summary = summarize_results(results)
avg_conf = sum(r.get("confidence", 0) for r in results) / max(len(results), 1)

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Invoices", summary["total"])
m2.metric("Auto-pass", summary["clean"])
m3.metric("Exceptions", summary["exceptions"])
m4.metric("Human review", summary["review_required"])
m5.metric("Avg confidence", f"{avg_conf:.0%}")

rows = [
    {
        "Invoice": r["invoice_id"],
        "Status": r["status"],
        "Route": r.get("route", "HUMAN_REVIEW" if r["human_review_required"] else "AUTO_PASS"),
        "Confidence": r.get("confidence", 0),
        "Rules": ", ".join(r["rule_ids"]) or "None",
    }
    for r in results
]
display_df = pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# Command Center
# ---------------------------------------------------------------------------
if st.session_state.active_view == "Command Center":
    st.markdown('<div class="fs-section">Control center</div>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        status_filter = st.selectbox("Status", ["ALL", "CLEAN", "EXCEPTION"])
    with f2:
        route_filter = st.selectbox("Route", ["ALL", "AUTO_PASS", "HUMAN_REVIEW", "EXCEPTION"])
    with f3:
        search = st.text_input("Search", placeholder="Invoice ID, rule or vendor…")

    filtered = display_df.copy()
    if status_filter != "ALL":
        filtered = filtered[filtered["Status"] == status_filter]
    if route_filter != "ALL":
        filtered = filtered[filtered["Route"] == route_filter]
    if search:
        mask = filtered.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        filtered = filtered[mask]

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1, format="%.0f%%"),
        },
    )

    c1, c2 = st.columns([1.25, .75])
    with c1:
        st.markdown('<div class="fs-section">Decision flow</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="fs-card"><b>Source</b> → <b>Rules</b> → <b>Evidence</b> → <b>Route</b> → <b>Human / AI explanation</b><br><br>'
            f'<span class="fs-mini">The deterministic engine remains the source of truth. Gemini receives trusted analysis only.</span></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown('<div class="fs-section">Quick actions</div>', unsafe_allow_html=True)
        if st.button("Open AI Copilot", use_container_width=True):
            st.session_state.active_view = "AI Copilot"
            st.rerun()
        if st.button("Open Review Queue", use_container_width=True):
            st.session_state.active_view = "Review Queue"
            st.rerun()

# ---------------------------------------------------------------------------
# AI Copilot
# ---------------------------------------------------------------------------
elif st.session_state.active_view == "AI Copilot":
    st.markdown(
        """
<div class="fs-chat-hero">
  <div class="fs-orb">✦</div>
  <div class="fs-chat-title">FinSight Copilot</div>
  <div class="fs-chat-copy">
    Ask about the current invoice analysis in natural language. Direct AP questions are
    answered deterministically; broader explanations can use Gemini over trusted evidence.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    qcols = st.columns(3)
    suggestions = [
        "Summarize this batch",
        "Which invoices need human review?",
        "Explain the exceptions",
    ]
    for col, suggestion in zip(qcols, suggestions):
        with col:
            if st.button(suggestion, use_container_width=True):
                st.session_state.chat.append(("user", suggestion))
                answer, mode = ask_gemini(suggestion, results, st.session_state.chat)
                st.session_state.chat.append(("assistant", answer))
                st.session_state.audit.append({
                    "timestamp": pd.Timestamp.now().isoformat(),
                    "event": "AI_QUERY",
                    "invoice_id": "",
                    "message": f"{mode}: {suggestion}",
                })
                save_audit_event("AI_QUERY", "", f"{mode}: {suggestion}")
                st.rerun()

    for role, msg in st.session_state.chat:
        with st.chat_message(role):
            st.write(msg)

    question = st.chat_input("Ask FinSight about an invoice, exception, rule or decision…")
    if question:
        st.session_state.chat.append(("user", question))
        answer, mode = ask_gemini(question, results, st.session_state.chat)
        st.session_state.chat.append(("assistant", answer))
        st.session_state.audit.append({
            "timestamp": pd.Timestamp.now().isoformat(),
            "event": "AI_QUERY",
            "invoice_id": "",
            "message": f"{mode}: {question}",
        })
        save_audit_event("AI_QUERY", "", f"{mode}: {question}")
        st.rerun()

# ---------------------------------------------------------------------------
# Review Queue
# ---------------------------------------------------------------------------
elif st.session_state.active_view == "Review Queue":
    review_items = [r for r in results if r["human_review_required"]]
    st.markdown('<div class="fs-section">Human review queue</div>', unsafe_allow_html=True)
    st.caption(f"{len(review_items)} item(s) are waiting for a reviewer decision.")

    if not review_items:
        st.success("Review queue is clear.")
    for r in review_items:
        iid = str(r["invoice_id"])
        current = st.session_state.reviews.get(iid, {})
        with st.container(border=True):
            st.markdown(f"### {iid}  ·  {r.get('confidence', 0):.0%} confidence")
            st.write(explain_invoice(r))
            for reason in r["reasons"]:
                st.markdown(f"**{reason['rule']}** — {reason['message']}")
            comment = st.text_input("Reviewer note", value=current.get("comment", ""), key=f"comment_{iid}")
            c1, c2, c3 = st.columns([1, 1, 3])
            with c1:
                if st.button("Approve", key=f"approve_{iid}", use_container_width=True):
                    st.session_state.reviews[iid] = {
                        "action": "APPROVED",
                        "comment": comment,
                        "timestamp": pd.Timestamp.now().isoformat(),
                    }
                    st.session_state.audit.append({
                        "timestamp": pd.Timestamp.now().isoformat(),
                        "event": "REVIEW",
                        "invoice_id": iid,
                        "message": f"APPROVED: {comment}",
                    })
                    save_review_action(iid, "APPROVED", comment)
                    st.rerun()
            with c2:
                if st.button("Reject", key=f"reject_{iid}", use_container_width=True):
                    st.session_state.reviews[iid] = {
                        "action": "REJECTED",
                        "comment": comment,
                        "timestamp": pd.Timestamp.now().isoformat(),
                    }
                    st.session_state.audit.append({
                        "timestamp": pd.Timestamp.now().isoformat(),
                        "event": "REVIEW",
                        "invoice_id": iid,
                        "message": f"REJECTED: {comment}",
                    })
                    save_review_action(iid, "REJECTED", comment)
                    st.rerun()
            with c3:
                if current:
                    st.caption(f"Latest action: **{current['action']}** · {current['timestamp']}")

# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------
elif st.session_state.active_view == "Evidence":
    st.markdown('<div class="fs-section">Evidence explorer</div>', unsafe_allow_html=True)
    by_id = {str(r["invoice_id"]): r for r in results}
    selected = st.selectbox("Invoice", list(by_id))
    r = by_id[selected]
    st.markdown(
        f'<div class="fs-card"><b>{selected}</b> · {r["status"]} · '
        f'{r.get("route", "HUMAN_REVIEW" if r["human_review_required"] else "AUTO_PASS")} · '
        f'{r.get("confidence", 0):.0%} confidence<br><br>'
        f'<span class="fs-mini">{explain_invoice(r)}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### Evidence")
    st.json(r["evidence"])
    st.markdown("#### Rule results")
    st.json(r["reasons"])

# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------
else:
    st.markdown('<div class="fs-section">Audit & export</div>', unsafe_allow_html=True)
    audit_df = pd.DataFrame(st.session_state.audit)
    if audit_df.empty:
        st.info("No audit events yet.")
    else:
        st.dataframe(audit_df, use_container_width=True, hide_index=True)

    export = [
        {
            "invoice_id": r["invoice_id"],
            "status": r["status"],
            "route": r.get("route"),
            "confidence": r.get("confidence"),
            "human_review_required": r["human_review_required"],
            "rule_ids": ", ".join(r["rule_ids"]),
            "reasons": " | ".join(x["message"] for x in r["reasons"]),
        }
        for r in results
    ]
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download results CSV",
            pd.DataFrame(export).to_csv(index=False),
            "finsight_results.csv",
            "text/csv",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "Download audit JSON",
            json.dumps(st.session_state.audit, indent=2, default=str),
            "finsight_audit.json",
            "application/json",
            use_container_width=True,
        )

st.divider()
st.caption("FinSight · deterministic controls · evidence-grounded AI · human-in-the-loop")
