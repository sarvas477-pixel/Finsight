"""FinSight — Streamlit AP intelligence workspace."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import CATEGORY_LIMITS, REQUIRED_COLUMNS
from src.rule_engine import process_invoices, summarize_results

st.set_page_config(
    page_title="FinSight — AP Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#f7f5f2;--paper:#fff;--ink:#202124;--muted:#77736e;--line:#e9e5df;--accent:#e34f62;--accent-soft:#fff0f2;--green:#16856f;--green-soft:#eaf8f3;--amber:#a96d19;--amber-soft:#fff6e5;--shadow:0 12px 35px rgba(31,29,25,.07)}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;color:var(--ink)}
.stApp{background:var(--bg)} .block-container{max-width:1480px;padding:28px 42px 70px}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.045em}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line)}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:22px;padding:16px 18px;box-shadow:var(--shadow)}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:18px;overflow:hidden}
div.stButton>button,div.stDownloadButton>button{min-height:42px;border-radius:999px;border:1px solid var(--line);font-weight:700;background:#fff}
button[kind="primary"]{background:var(--accent)!important;color:#fff!important;border:0!important}
.fs-brand{font-family:'Space Grotesk';font-size:1.35rem;font-weight:700;letter-spacing:-.05em}.fs-brand span{color:var(--accent)}
.fs-eyebrow{font-size:.72rem;text-transform:uppercase;letter-spacing:.16em;font-weight:800;color:var(--accent)}
.fs-hero{background:#fff;border:1px solid var(--line);border-radius:30px;padding:38px;box-shadow:var(--shadow);position:relative;overflow:hidden}
.fs-hero:after{content:"";position:absolute;width:260px;height:260px;border-radius:50%;right:-100px;top:-120px;background:var(--accent-soft)}
.fs-title{font-family:'Space Grotesk';font-size:clamp(2.5rem,5vw,4.8rem);line-height:.92;letter-spacing:-.075em;max-width:900px;margin:10px 0 18px}
.fs-copy{max-width:760px;color:var(--muted);font-size:1.03rem;line-height:1.65}
.fs-pills{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}.fs-pill{padding:8px 12px;border:1px solid var(--line);border-radius:999px;background:#fff;font-size:.78rem;font-weight:700}
.fs-section{font-family:'Space Grotesk';font-size:1.35rem;font-weight:700;letter-spacing:-.04em;margin:32px 0 12px}
.fs-card{background:#fff;border:1px solid var(--line);border-radius:24px;padding:22px;box-shadow:var(--shadow)}
.fs-step{min-height:120px;background:#fff;border:1px solid var(--line);border-radius:22px;padding:20px}
.fs-step-no{font-size:.72rem;font-weight:800;color:var(--accent);letter-spacing:.12em}.fs-step-title{font-family:'Space Grotesk';font-size:1.08rem;font-weight:700;margin:7px 0}.fs-sub{color:var(--muted);font-size:.88rem}
.fs-status{display:inline-block;padding:6px 10px;border-radius:999px;font-size:.72rem;font-weight:800}.fs-clean{background:var(--green-soft);color:var(--green)}.fs-exception{background:var(--accent-soft);color:#a73547}.fs-review{background:var(--amber-soft);color:var(--amber)}.fs-neutral{background:#f0eeeb;color:#5d5954}
.fs-footer{text-align:center;color:#96918a;font-size:.76rem;margin-top:48px}
</style>
""",
    unsafe_allow_html=True,
)


def init_state() -> None:
    defaults = {"df": None, "source_name": "", "results": [], "analyzed": False,
                "audit": [], "reviews": {}, "chat": []}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_workspace(df: pd.DataFrame | None = None, source_name: str = "") -> None:
    st.session_state.df = df
    st.session_state.source_name = source_name
    st.session_state.results = []
    st.session_state.analyzed = False
    st.session_state.audit = []
    st.session_state.reviews = {}
    st.session_state.chat = []


def load_sample() -> pd.DataFrame:
    path = ROOT / "data" / "invoices.csv"
    if not path.exists():
        raise FileNotFoundError("Bundled sample data/invoices.csv is missing.")
    return pd.read_csv(path)


def add_audit(event: str, invoice_id: str = "", message: str = "", metadata: dict | None = None) -> None:
    st.session_state.audit.append({
        "timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "event": event,
        "invoice_id": str(invoice_id),
        "message": message,
    })
    try:
        from src.persistence import save_audit_event
        save_audit_event(event, invoice_id, message, metadata)
    except Exception:
        pass


def analyze(df: pd.DataFrame) -> list[dict]:
    return process_invoices(df)


def build_results_df(results: list[dict]) -> pd.DataFrame:
    rows = []
    for item in results:
        evidence = item.get("evidence") or {}
        reasons = item.get("reasons") or []
        rows.append({
            "invoice_id": item.get("invoice_id"),
            "vendor": evidence.get("vendor"),
            "amount": evidence.get("amount"),
            "category": evidence.get("category"),
            "invoice_date": evidence.get("invoice_date"),
            "status": item.get("status"),
            "route": item.get("route"),
            "confidence": float(item.get("confidence", 0)),
            "human_review_required": bool(item.get("human_review_required")),
            "rule_ids": ", ".join(item.get("rule_ids") or []),
            "reasons": " | ".join(str(r.get("message", "")) for r in reasons),
            "matched_invoice_id": evidence.get("matched_invoice_id"),
        })
    return pd.DataFrame(rows)


def explain(item: dict) -> str:
    iid = item.get("invoice_id", "Invoice")
    if item.get("status") == "CLEAN":
        return f"{iid} passed all configured checks and is AUTO-PASS with {float(item.get('confidence',1)):.0%} confidence."
    reason_text = " ".join(str(x.get("message", "")) for x in item.get("reasons", []))
    return f"{iid} is {item.get('status','EXCEPTION')} and routed to {item.get('route','HUMAN_REVIEW')}. {reason_text}"


def badge(status: str, review: bool) -> str:
    if status == "CLEAN":
        return "fs-clean"
    return "fs-review" if review else "fs-exception"


def copilot(question: str) -> tuple[str, str]:
    try:
        from src.ai import ask_gemini
        return ask_gemini(question, st.session_state.results, st.session_state.chat)
    except Exception as exc:
        return f"Copilot fallback is active ({type(exc).__name__}). The deterministic analysis is still available.", "fallback"


def record_review(invoice_id: str, action: str, comment: str) -> None:
    st.session_state.reviews[invoice_id] = {
        "action": action, "comment": comment.strip(),
        "timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
    }
    add_audit("REVIEW_ACTION", invoice_id, f"{action}: {comment.strip()}".strip())
    try:
        from src.persistence import save_review_action
        save_review_action(invoice_id, action, comment.strip())
    except Exception:
        pass


def sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="fs-brand">✦ <span>Fin</span>sight</div>', unsafe_allow_html=True)
        st.caption("Accounts-payable intelligence")
        st.divider()
        uploaded = st.file_uploader("Upload invoice CSV", type=["csv"],
                                    help="Required: invoice_id, vendor, amount, category, invoice_date")
        if uploaded is not None and uploaded.name != st.session_state.source_name:
            try:
                frame = pd.read_csv(uploaded)
                reset_workspace(frame, uploaded.name)
                st.toast(f"Loaded {len(frame):,} rows", icon="✦")
            except Exception as exc:
                st.error(f"Could not read CSV: {exc}")
        if st.button("Use sample data", use_container_width=True):
            try:
                reset_workspace(load_sample(), "data/invoices.csv")
                st.toast("Sample invoices loaded", icon="✦")
            except Exception as exc:
                st.error(str(exc))
        if st.button("Reset workspace", use_container_width=True):
            reset_workspace()
            st.rerun()
        st.divider()
        st.markdown("**Process**")
        for n, label in [("01","Upload CSV"),("02","Analyze"),("03","Human review"),("04","Audit log"),("05","FinSight Copilot")]:
            st.markdown(f'<div style="padding:6px 0"><span class="fs-step-no">{n}</span> <b>{label}</b></div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("**Category limits**")
        for category, limit in CATEGORY_LIMITS.items():
            st.caption(f"{category} · ₹{limit:,.0f}")


def hero() -> None:
    st.markdown(
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">'
        '<div class="fs-brand">✦ <span>Fin</span>sight</div><div class="fs-eyebrow">AP intelligence workspace</div></div>'
        '<div class="fs-hero">'
        '<div class="fs-eyebrow">Invoice intelligence / human in the loop</div>'
        '<div class="fs-title">Turn the exception pile into a clear next step.</div>'
        '<div class="fs-copy">Upload a CSV, run deterministic controls, see exactly why an invoice was flagged, '
        'send uncertain cases to human review, keep an audit trail, and ask FinSight Copilot questions grounded in the analyzed evidence.</div>'
        '<div class="fs-pills"><span class="fs-pill">01 Upload</span><span class="fs-pill">02 Analyze</span>'
        '<span class="fs-pill">03 Review</span><span class="fs-pill">04 Audit</span><span class="fs-pill">05 Copilot</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )


def empty_state() -> None:
    st.markdown('<div class="fs-section">Start with a CSV</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    steps = [("01","Upload","Bring invoice data into the workspace."),("02","Analyze","Run the validation engine."),
             ("03","Review","Handle flagged invoices."),("04","Audit","Track decisions and actions."),("05","Copilot","Ask grounded questions.")]
    for col, (n, title, body) in zip(cols, steps):
        with col:
            st.markdown(f'<div class="fs-step"><div class="fs-step-no">{n}</div><div class="fs-step-title">{title}</div><div class="fs-sub">{body}</div></div>', unsafe_allow_html=True)
    st.info("Upload an invoice CSV from the sidebar or use the bundled sample data.")
    st.markdown('<div class="fs-section">FinSight Copilot</div>', unsafe_allow_html=True)
    copilot_tab()


def summary(results: list[dict]) -> None:
    s = summarize_results(results)
    avg = sum(float(x.get("confidence", 0)) for x in results) / len(results)
    a,b,c,d,e = st.columns(5)
    a.metric("Invoices", s["total"]); b.metric("Auto-pass", s["clean"]); c.metric("Exceptions", s["exceptions"])
    d.metric("Human review", s["review_required"]); e.metric("Avg confidence", f"{avg:.0%}")


def results_section(df: pd.DataFrame, results: list[dict]) -> None:
    st.markdown('<div class="fs-section">Analysis results</div>', unsafe_allow_html=True)
    summary(results)
    out = build_results_df(results)
    exceptions = out[out["status"] == "EXCEPTION"].copy()

    st.markdown('<div class="fs-card">', unsafe_allow_html=True)
    st.markdown("**Decision table**")
    st.caption("Source of truth: the deterministic rule engine.")
    st.dataframe(out[["invoice_id","vendor","amount","category","status","route","confidence","rule_ids"]],
                 use_container_width=True, hide_index=True,
                 column_config={"confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1, format="%.0f%%")})
    st.markdown("</div>", unsafe_allow_html=True)

    x,y,z = st.columns(3)
    with x:
        st.download_button("Download analyzed CSV", out.to_csv(index=False).encode(), "finsight_analyzed_invoices.csv", "text/csv", use_container_width=True)
    with y:
        st.download_button(f"Download exceptions ({len(exceptions)})", exceptions.to_csv(index=False).encode(), "finsight_exceptions.csv", "text/csv", use_container_width=True)
    with z:
        st.download_button("Download original CSV", df.to_csv(index=False).encode(), "finsight_original_invoices.csv", "text/csv", use_container_width=True)

    st.markdown('<div class="fs-section">Invoice decisions</div>', unsafe_allow_html=True)
    for item in results[:12]:
        cls = badge(str(item.get("status")), bool(item.get("human_review_required")))
        st.markdown(
            f'<div class="fs-card" style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;gap:12px">'
            f'<div><b>{item.get("invoice_id")}</b> <span class="fs-status {cls}">{item.get("status")}</span> '
            f'<span class="fs-status fs-neutral">{item.get("route")}</span></div><b>{float(item.get("confidence",0)):.0%}</b></div>'
            f'<div class="fs-sub" style="margin-top:10px">{explain(item)}</div></div>',
            unsafe_allow_html=True,
        )
    if len(results) > 12:
        st.caption(f"Showing 12 of {len(results)} decisions. Use Evidence for the full set.")


def review_tab(results: list[dict]) -> None:
    items = [x for x in results if x.get("human_review_required")]
    st.markdown('<div class="fs-section">Human review queue</div>', unsafe_allow_html=True)
    if not items:
        st.success("No invoices currently require human review.")
        return
    st.warning(f"{len(items)} invoice(s) need a human decision.")
    for item in items:
        iid = str(item.get("invoice_id"))
        old = st.session_state.reviews.get(iid, {})
        with st.container(border=True):
            left,right = st.columns([4,1])
            with left:
                st.markdown(f"### {iid}")
                st.write(explain(item))
                for reason in item.get("reasons", []):
                    st.markdown(f"**{reason.get('rule')}** · {reason.get('message')}")
            with right:
                st.metric("Confidence", f"{float(item.get('confidence',0)):.0%}")
            note = st.text_area("Reviewer note", value=old.get("comment",""), key=f"note_{iid}")
            a,b = st.columns(2)
            with a:
                if st.button("Approve invoice", key=f"approve_{iid}", use_container_width=True):
                    record_review(iid, "APPROVED", note); st.success(f"{iid} approved.")
            with b:
                if st.button("Reject invoice", key=f"reject_{iid}", use_container_width=True):
                    record_review(iid, "REJECTED", note); st.warning(f"{iid} rejected.")
            if iid in st.session_state.reviews:
                st.caption(f"Latest action: {st.session_state.reviews[iid]['action']}")


def evidence_tab(results: list[dict]) -> None:
    st.markdown('<div class="fs-section">Evidence explorer</div>', unsafe_allow_html=True)
    ids = [str(x.get("invoice_id")) for x in results]
    selected = st.selectbox("Invoice", ids)
    item = next(x for x in results if str(x.get("invoice_id")) == selected)
    a,b,c = st.columns(3)
    a.metric("Status", item.get("status","—")); b.metric("Route", item.get("route","—")); c.metric("Confidence", f"{float(item.get('confidence',0)):.0%}")
    st.markdown('<div class="fs-card">', unsafe_allow_html=True)
    st.markdown("### Decision explanation"); st.write(explain(item))
    st.markdown("</div>", unsafe_allow_html=True)
    x,y = st.columns(2)
    with x:
        st.markdown("#### Trusted evidence"); st.json(item.get("evidence", {}))
    with y:
        st.markdown("#### Triggered rules"); st.json(item.get("reasons", []))


def audit_tab(results: list[dict]) -> None:
    st.markdown('<div class="fs-section">Audit log & export</div>', unsafe_allow_html=True)
    st.caption("The local session audit always works. Supabase persistence is optional.")
    audit_df = pd.DataFrame(st.session_state.audit)
    if audit_df.empty:
        st.info("No audit events yet.")
    else:
        st.dataframe(audit_df, use_container_width=True, hide_index=True)
    out = build_results_df(results); exceptions = out[out["status"] == "EXCEPTION"]
    a,b,c = st.columns(3)
    with a: st.download_button("Analyzed CSV", out.to_csv(index=False).encode(), "finsight_analyzed_invoices.csv", "text/csv", use_container_width=True, key="audit_csv")
    with b: st.download_button("Exceptions CSV", exceptions.to_csv(index=False).encode(), "finsight_exceptions.csv", "text/csv", use_container_width=True, key="audit_exceptions")
    with c: st.download_button("Audit JSON", json.dumps(st.session_state.audit, indent=2, default=str).encode(), "finsight_audit.json", "application/json", use_container_width=True, key="audit_json")
    if st.button("Check optional connections", use_container_width=True):
        try:
            from src.ai import test_gemini_connection
            ok,msg = test_gemini_connection(); (st.success if ok else st.warning)(f"Gemini: {msg}")
        except Exception as exc: st.warning(f"Gemini check unavailable: {exc}")
        try:
            from src.persistence import test_supabase_connection
            ok,msg = test_supabase_connection(); (st.success if ok else st.warning)(f"Supabase: {msg}")
        except Exception as exc: st.warning(f"Supabase check unavailable: {exc}")


def copilot_tab() -> None:
    st.markdown('<div class="fs-section">FinSight Copilot</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="fs-card"><div class="fs-eyebrow">General AI + FinSight intelligence</div>'
        '<h2>Ask anything.</h2><div class="fs-sub">Ask about invoices or switch topics completely — '
        'coding, study, science, writing, technology, ideas, or everyday questions. '
        'Invoice decisions remain controlled by the deterministic rule engine.</div></div>',
        unsafe_allow_html=True,
    )
    prompts = [
        "Summarize this batch",
        "Which invoices need human review?",
        "Explain the exceptions",
        "Explain Python lists simply",
    ]
    cols = st.columns(4)
    for col, prompt in zip(cols, prompts):
        with col:
            if st.button(prompt, key=f"quick_{prompt}", use_container_width=True):
                answer, mode = copilot(prompt)
                st.session_state.chat += [("user", prompt), ("assistant", answer)]
                add_audit("AI_QUERY", "", f"{mode}: {prompt}")
                st.rerun()
    for role, message in st.session_state.chat:
        with st.chat_message(role):
            st.write(message)
    question = st.chat_input("Ask anything — invoice, coding, study, science, writing, or general knowledge...")
    if question:
        answer, mode = copilot(question)
        st.session_state.chat += [("user", question), ("assistant", answer)]
        add_audit("AI_QUERY", "", f"{mode}: {question}")
        st.rerun()

def workspace() -> None:
    df = st.session_state.df
    st.markdown('<div class="fs-section">Workspace</div>', unsafe_allow_html=True)
    st.caption(f"Source: {st.session_state.source_name or 'uploaded CSV'} · {len(df):,} row(s) · required: {', '.join(REQUIRED_COLUMNS)}")
    a,b = st.columns([1,3])
    with a: run = st.button("Analyze invoices", type="primary", use_container_width=True)
    with b: st.markdown('<div class="fs-sub" style="padding:10px 0">Results appear immediately below. No second page or manual refresh.</div>', unsafe_allow_html=True)
    with st.expander("Preview uploaded CSV", expanded=not st.session_state.analyzed):
        st.dataframe(df.head(100), use_container_width=True, hide_index=True)

    if run:
        try:
            with st.spinner("Analyzing invoices..."):
                results = analyze(df)
            st.session_state.results = results; st.session_state.analyzed = True
            st.session_state.audit = []; st.session_state.reviews = {}; st.session_state.chat = []
            for item in results:
                add_audit("DECISION", str(item.get("invoice_id")),
                          f"{item.get('status')} / {item.get('route')} / {float(item.get('confidence',0)):.0%}",
                          {"rule_ids": item.get("rule_ids", [])})
            st.success(f"Analysis complete — {len(results):,} invoice(s) checked.")
        except Exception as exc:
            st.error(f"Analysis failed safely: {exc}")
            return

    if not st.session_state.analyzed:
        st.info("Click Analyze invoices to begin.")
        return

    results_section(df, st.session_state.results)
    tabs = st.tabs(["Human review","Evidence","Audit log","FinSight Copilot"])
    with tabs[0]: review_tab(st.session_state.results)
    with tabs[1]: evidence_tab(st.session_state.results)
    with tabs[2]: audit_tab(st.session_state.results)
    with tabs[3]: copilot_tab()


init_state()
sidebar()
hero()

if st.session_state.df is None:
    empty_state()
elif st.session_state.df.empty:
    st.error("The CSV contains no invoice rows.")
else:
    workspace()

st.markdown('<div class="fs-footer">FinSight · deterministic controls · human-in-the-loop · evidence-grounded Copilot</div>', unsafe_allow_html=True)
