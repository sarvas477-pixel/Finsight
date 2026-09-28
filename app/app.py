import sys
from pathlib import Path
import json

import pandas as pd
import streamlit as st

# Make "src" importable regardless of where Streamlit is launched from.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import REQUIRED_COLUMNS, CATEGORY_LIMITS
from src.rule_engine import process_invoices, summarize_results


st.set_page_config(
    page_title="FinSight | Invoice Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--ink:#172033;--muted:#6b7589;--paper:#f7f8fc;--line:#e7eaf1;--blue:#3157e8;--blue2:#5575ee}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;color:var(--ink)}
.stApp{background:radial-gradient(circle at 8% 0%,rgba(49,87,232,.08),transparent 28%),radial-gradient(circle at 96% 10%,rgba(15,159,154,.08),transparent 25%),var(--paper)}
.block-container{max-width:1480px;padding-top:1.6rem;padding-bottom:4rem}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.04em}
[data-testid="stSidebar"]{background:rgba(255,255,255,.94);border-right:1px solid var(--line)}
div.stButton>button,div.stDownloadButton>button{border-radius:12px;border:1px solid var(--line);min-height:42px;font-weight:600}
button[kind="primary"]{background:linear-gradient(135deg,var(--blue),var(--blue2))!important;color:#fff!important;border:0!important}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px 18px}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:15px;overflow:hidden}
.fs-hero{padding:32px 36px;border-radius:26px;background:linear-gradient(110deg,#fff,#f5f8ff);border:1px solid var(--line);box-shadow:0 18px 50px rgba(31,44,79,.08)}
.kicker{color:var(--blue);font-size:.76rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase}
.hero-title{font-family:'Space Grotesk';font-size:clamp(2rem,4vw,3.6rem);line-height:.98;letter-spacing:-.065em;margin:8px 0 12px}
.hero-copy{color:var(--muted);max-width:800px;font-size:1.02rem}
.pill{display:inline-block;padding:7px 11px;margin:8px 5px 0 0;border:1px solid var(--line);border-radius:999px;background:#fff;font-size:.78rem;font-weight:600}
.card,.result-card{background:#fff;border:1px solid var(--line);border-radius:20px;padding:20px;box-shadow:0 10px 34px rgba(31,44,79,.055)}
.section{font-family:'Space Grotesk';font-weight:700;font-size:1.1rem;margin:25px 0 10px}
.muted{color:var(--muted);font-size:.84rem}
.status{display:inline-block;padding:6px 10px;border-radius:999px;font-size:.75rem;font-weight:700;margin-left:5px}
.clean{color:#087c6e;background:#e9faf7}.exception{color:#a3454d;background:#fff0f1}.review{color:#95651b;background:#fff7e8}
</style>
""", unsafe_allow_html=True)


def init_state():
    defaults = {
        "df": None,
        "results": [],
        "analyzed": False,
        "chat": [],
        "reviews": {},
        "audit": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_sample():
    sample = ROOT / "data" / "invoices.csv"
    if not sample.exists():
        raise FileNotFoundError(f"Sample file not found: {sample}")
    return pd.read_csv(sample)


def reset_analysis(df):
    st.session_state.df = df
    st.session_state.results = []
    st.session_state.analyzed = False
    st.session_state.chat = []
    st.session_state.reviews = {}
    st.session_state.audit = []


def build_analysis_dataframe(results):
    rows = []
    for r in results:
        evidence = r.get("evidence") or {}
        reasons = r.get("reasons") or []
        rows.append({
            "invoice_id": r.get("invoice_id"),
            "vendor": evidence.get("vendor"),
            "amount": evidence.get("amount"),
            "category": evidence.get("category"),
            "invoice_date": evidence.get("invoice_date"),
            "status": r.get("status"),
            "route": r.get("route"),
            "confidence": r.get("confidence"),
            "human_review_required": r.get("human_review_required"),
            "rule_ids": ", ".join(r.get("rule_ids") or []),
            "reasons": " | ".join(str(x.get("message", "")) for x in reasons),
            "matched_invoice_id": evidence.get("matched_invoice_id"),
        })
    return pd.DataFrame(rows)


def save_audit_local(event, invoice_id="", message=""):
    st.session_state.audit.append({
        "timestamp": pd.Timestamp.now().isoformat(),
        "event": event,
        "invoice_id": str(invoice_id),
        "message": message,
    })


def optional_persistence(event_type, invoice_id, message, metadata=None):
    """Never let optional Supabase integration stop the UI."""
    try:
        from src.persistence import save_audit_event
        return save_audit_event(event_type, invoice_id, message, metadata)
    except Exception:
        return False, "Optional persistence unavailable."


def optional_ai(question, results, conversation):
    """Use existing AI module only when the user actually asks for AI."""
    try:
        from src.ai import ask_gemini
        return ask_gemini(question, results, conversation)
    except Exception as exc:
        return (
            "AI integration is unavailable right now. The deterministic invoice "
            f"analysis is still working. ({type(exc).__name__})",
            "fallback",
        )


def explain_result(r):
    if r.get("status") == "CLEAN":
        return (
            f"{r.get('invoice_id')} passed all configured deterministic checks "
            f"and is routed to AUTO_PASS with {float(r.get('confidence', 1)):.0%} confidence."
        )
    reasons = r.get("reasons") or []
    text = " ".join(str(x.get("message", "")) for x in reasons)
    return (
        f"{r.get('invoice_id')} is {r.get('status')} and routed to "
        f"{r.get('route', 'HUMAN_REVIEW')}. {text}"
    )


init_state()

# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown("## ✦ FinSight")
    st.caption("Invoice intelligence workspace")
    st.divider()

    uploaded = st.file_uploader("Upload invoice CSV", type=["csv"])

    if st.button("Use sample invoices", use_container_width=True):
        try:
            reset_analysis(load_sample())
            st.toast("Sample invoices loaded", icon="✦")
        except Exception as exc:
            st.error(f"Could not load sample invoices: {exc}")

    if st.button("Reset workspace", use_container_width=True):
        reset_analysis(None)
        st.rerun()

    st.divider()
    view = st.radio(
        "Navigate",
        ["Command Center", "AI Copilot", "Review Queue", "Evidence", "Audit & Export"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Configured limits**")
    for category, limit in CATEGORY_LIMITS.items():
        st.caption(f"{category} · ₹{limit:,.0f}")

if uploaded is not None:
    try:
        new_df = pd.read_csv(uploaded)
        if st.session_state.df is None or st.session_state.get("uploaded_name") != uploaded.name:
            reset_analysis(new_df)
            st.session_state.uploaded_name = uploaded.name
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}")

df = st.session_state.df

# ---------------- Hero ----------------
st.markdown("""
<div class="fs-hero">
  <div class="kicker">Accounts payable · intelligence layer</div>
  <div class="hero-title">From invoice upload<br>to an explainable decision.</div>
  <div class="hero-copy">
    Validate invoices with deterministic controls, inspect evidence, route uncertain
    cases to human review, and export the analyzed dataset.
  </div>
  <span class="pill">✦ Evidence first</span>
  <span class="pill">◉ Human review</span>
  <span class="pill">↗ Audit ready</span>
  <span class="pill">⌁ AI copilot</span>
</div>
""", unsafe_allow_html=True)

if df is None:
    st.markdown('<div class="section">Start here</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    for col, title, copy in [
        (a, "01 · Upload", "Upload your invoice CSV or use the sample dataset."),
        (b, "02 · Analyze", "Run the deterministic validation engine."),
        (c, "03 · Review", "Inspect results, evidence and downloadable outputs."),
    ]:
        with col:
            st.markdown(
                f'<div class="card"><b>{title}</b><br><span class="muted">{copy}</span></div>',
                unsafe_allow_html=True,
            )
    st.info("Upload a CSV or click Use sample invoices to begin.")
    st.stop()

if df.empty:
    st.error("The CSV contains no invoice rows.")
    st.stop()

# ---------------- Analysis ----------------
st.markdown('<div class="section">Analysis workspace</div>', unsafe_allow_html=True)
c1, c2 = st.columns([4, 1])
with c1:
    st.markdown(
        f'<span class="muted"><b>{len(df):,}</b> invoice row(s) loaded · '
        f'required fields: {", ".join(REQUIRED_COLUMNS)}</span>',
        unsafe_allow_html=True,
    )
with c2:
    analyze = st.button("Analyze invoices", type="primary", use_container_width=True)

with st.expander("Preview uploaded CSV", expanded=not st.session_state.analyzed):
    st.dataframe(df.head(100), use_container_width=True, hide_index=True)

if analyze:
    try:
        with st.spinner("Analyzing invoices…"):
            results = process_invoices(df)
        st.session_state.results = results
        st.session_state.analyzed = True
        st.session_state.chat = []
        st.session_state.audit = []
        for r in results:
            save_audit_local(
                "DECISION",
                r.get("invoice_id"),
                f"{r.get('status')} / {r.get('route')} / {float(r.get('confidence', 0)):.0%}",
            )
        st.toast(f"{len(results)} invoices analyzed", icon="✅")
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")
        st.stop()

if not st.session_state.analyzed:
    st.info("Click Analyze invoices. Results will appear directly below.")
    st.stop()

results = st.session_state.results
if not results:
    st.warning("Analysis returned no results.")
    st.stop()

# ---------------- Always-visible results ----------------
summary = summarize_results(results)
analysis_df = build_analysis_dataframe(results)
exceptions_df = analysis_df[analysis_df["status"] == "EXCEPTION"].copy()
avg_conf = sum(float(r.get("confidence", 0)) for r in results) / len(results)

st.markdown('<div class="section">Analysis results</div>', unsafe_allow_html=True)
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Invoices", summary["total"])
m2.metric("Auto-pass", summary["clean"])
m3.metric("Exceptions", summary["exceptions"])
m4.metric("Human review", summary["review_required"])
m5.metric("Avg confidence", f"{avg_conf:.0%}")

rows = []
for r in results:
    rows.append({
        "Invoice": str(r.get("invoice_id", "")),
        "Status": str(r.get("status", "")),
        "Route": str(r.get("route", "")),
        "Confidence": float(r.get("confidence", 0)),
        "Rules": ", ".join(r.get("rule_ids", [])) or "None",
    })
result_df = pd.DataFrame(rows)

st.markdown("#### Result table")
st.dataframe(
    result_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Confidence": st.column_config.ProgressColumn(
            "Confidence", min_value=0, max_value=1, format="%.0f%%"
        )
    },
)

st.markdown("#### Analyzed CSV preview")
st.caption(
    "The analyzed export combines the original invoice fields with FinSight's "
    "status, route, confidence, rules, reasons and duplicate evidence."
)
st.dataframe(
    analysis_df,
    use_container_width=True,
    hide_index=True,
    height=min(620, max(260, 58 + len(analysis_df) * 35)),
)

d1, d2 = st.columns(2)
with d1:
    st.download_button(
        "⬇ Download analyzed CSV",
        analysis_df.to_csv(index=False).encode("utf-8"),
        "finsight_analyzed_invoices.csv",
        "text/csv",
        use_container_width=True,
        key="download_analyzed_main",
    )
with d2:
    st.download_button(
        f"⬇ Download exceptions CSV ({len(exceptions_df)})",
        exceptions_df.to_csv(index=False).encode("utf-8"),
        "finsight_exceptions.csv",
        "text/csv",
        use_container_width=True,
        key="download_exceptions_main",
    )

st.markdown('<div class="section">Invoice decisions</div>', unsafe_allow_html=True)
for r in results[:8]:
    status = str(r.get("status", "UNKNOWN"))
    cls = "clean" if status == "CLEAN" else ("review" if r.get("human_review_required") else "exception")
    st.markdown(
        f'<div class="result-card"><b>{r.get("invoice_id")}</b>'
        f'<span class="status {cls}">{status}</span>'
        f'<span class="status">{r.get("route", "")}</span>'
        f'<span class="status">{float(r.get("confidence", 0)):.0%}</span>'
        f'<br><span class="muted">{explain_result(r)}</span></div><br>',
        unsafe_allow_html=True,
    )
if len(results) > 8:
    st.caption(f"Showing 8 of {len(results)} decision cards. Use Evidence for any invoice.")

# ---------------- Secondary workspace ----------------
st.markdown('<div class="section">Workspace</div>', unsafe_allow_html=True)

if view == "Command Center":
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        status_filter = st.selectbox("Status", ["ALL", "CLEAN", "EXCEPTION"])
    with f2:
        route_filter = st.selectbox("Route", ["ALL", "AUTO_PASS", "HUMAN_REVIEW"])
    with f3:
        search = st.text_input("Search", placeholder="Invoice ID, rule or value")

    filtered = result_df.copy()
    if status_filter != "ALL":
        filtered = filtered[filtered["Status"] == status_filter]
    if route_filter != "ALL":
        filtered = filtered[filtered["Route"] == route_filter]
    if search:
        mask = filtered.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        filtered = filtered[mask]
    st.dataframe(filtered, use_container_width=True, hide_index=True)

elif view == "AI Copilot":
    st.markdown(
        '<div class="card"><h3>✦ FinSight Copilot</h3>'
        '<span class="muted">AI is optional and never controls the deterministic decision.</span></div>',
        unsafe_allow_html=True,
    )

    for question in [
        "Summarize this batch",
        "Which invoices need human review?",
        "Explain the exceptions",
    ]:
        if st.button(question, use_container_width=True, key=f"ai_{question}"):
            answer, mode = optional_ai(question, results, st.session_state.chat)
            st.session_state.chat.append(("user", question))
            st.session_state.chat.append(("assistant", answer))
            save_audit_local("AI_QUERY", "", f"{mode}: {question}")
            optional_persistence("AI_QUERY", "", f"{mode}: {question}")

    for role, message in st.session_state.chat:
        with st.chat_message(role):
            st.write(message)

    question = st.chat_input("Ask about an invoice, exception, rule or decision…")
    if question:
        answer, mode = optional_ai(question, results, st.session_state.chat)
        st.session_state.chat.append(("user", question))
        st.session_state.chat.append(("assistant", answer))
        save_audit_local("AI_QUERY", "", f"{mode}: {question}")
        optional_persistence("AI_QUERY", "", f"{mode}: {question}")
        st.rerun()

elif view == "Review Queue":
    review_items = [r for r in results if r.get("human_review_required")]
    st.markdown(
        f'<div class="card"><b>{len(review_items)} invoice(s)</b> require human review.</div>',
        unsafe_allow_html=True,
    )

    for r in review_items:
        iid = str(r.get("invoice_id"))
        current = st.session_state.reviews.get(iid, {})
        with st.container(border=True):
            st.markdown(f"### {iid} · {float(r.get('confidence', 0)):.0%} confidence")
            st.write(explain_result(r))
            for reason in r.get("reasons", []):
                st.markdown(f"**{reason.get('rule')}** — {reason.get('message')}")

            comment = st.text_input(
                "Reviewer note",
                value=current.get("comment", ""),
                key=f"comment_{iid}",
            )
            a, b = st.columns(2)
            with a:
                if st.button("Approve", key=f"approve_{iid}", use_container_width=True):
                    st.session_state.reviews[iid] = {
                        "action": "APPROVED",
                        "comment": comment,
                        "timestamp": pd.Timestamp.now().isoformat(),
                    }
                    save_audit_local("REVIEW_ACTION", iid, f"APPROVED: {comment}".strip())
                    optional_persistence("REVIEW_ACTION", iid, f"APPROVED: {comment}".strip())
                    st.toast(f"{iid} approved", icon="✅")
            with b:
                if st.button("Reject", key=f"reject_{iid}", use_container_width=True):
                    st.session_state.reviews[iid] = {
                        "action": "REJECTED",
                        "comment": comment,
                        "timestamp": pd.Timestamp.now().isoformat(),
                    }
                    save_audit_local("REVIEW_ACTION", iid, f"REJECTED: {comment}".strip())
                    optional_persistence("REVIEW_ACTION", iid, f"REJECTED: {comment}".strip())
                    st.toast(f"{iid} rejected", icon="⚠️")

    if not review_items:
        st.success("No invoices currently require human review.")

elif view == "Evidence":
    ids = [str(r.get("invoice_id")) for r in results]
    selected = st.selectbox("Select invoice", ids)
    r = next(r for r in results if str(r.get("invoice_id")) == selected)

    st.markdown(
        f'<div class="card"><h3>{selected}</h3>'
        f'<span class="muted">{r.get("status")} · {r.get("route")} · '
        f'{float(r.get("confidence", 0)):.0%} confidence</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### Explanation")
    st.write(explain_result(r))
    st.markdown("#### Evidence")
    st.json(r.get("evidence", {}))
    st.markdown("#### Rule results")
    st.json(r.get("reasons", []))

else:
    st.markdown(
        '<div class="card"><h3>Audit & Export</h3>'
        '<span class="muted">Events recorded during this browser session.</span></div>',
        unsafe_allow_html=True,
    )
    audit_df = pd.DataFrame(st.session_state.audit)
    if audit_df.empty:
        st.info("No audit events yet.")
    else:
        st.dataframe(audit_df, use_container_width=True, hide_index=True)

    a, b, c = st.columns(3)
    with a:
        st.download_button(
            "⬇ Analyzed CSV",
            analysis_df.to_csv(index=False).encode("utf-8"),
            "finsight_analyzed_invoices.csv",
            "text/csv",
            use_container_width=True,
            key="download_analyzed_audit",
        )
    with b:
        st.download_button(
            "⬇ Exceptions CSV",
            exceptions_df.to_csv(index=False).encode("utf-8"),
            "finsight_exceptions.csv",
            "text/csv",
            use_container_width=True,
            key="download_exceptions_audit",
        )
    with c:
        st.download_button(
            "⬇ Audit JSON",
            json.dumps(st.session_state.audit, indent=2, default=str).encode("utf-8"),
            "finsight_audit.json",
            "application/json",
            use_container_width=True,
            key="download_audit_json",
        )

st.divider()
st.caption("FinSight · deterministic controls · evidence-grounded AI · human-in-the-loop")
