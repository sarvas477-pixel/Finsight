"""FinSight — bright, action-first accounts-payable intelligence workspace."""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import CATEGORY_LIMITS, REQUIRED_COLUMNS
from src.rule_engine import process_invoices, summarize_results
from src.auth import require_login


st.set_page_config(
    page_title="FinSight · AP Intelligence",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#050914;--panel:#0b1628;--panel2:#0d1b30;--panel3:#101f35;--line:#1e2c44;--cyan:#00d9ff;--blue:#147bff;--violet:#715cff;--text:#f4f8ff;--muted:#b7c3d8;--steel:#65738b;--green:#35d07f;--amber:#f5b942;--red:#ff5c70}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:radial-gradient(circle at 85% 0%,rgba(0,217,255,.055),transparent 24%),radial-gradient(circle at 10% 85%,rgba(113,92,255,.055),transparent 26%),var(--bg)!important;color:var(--text)!important}
body,[class*="css"]{font-family:'Inter',sans-serif}
[data-testid="stHeader"]{background:rgba(5,9,20,.82)!important;border-bottom:1px solid rgba(0,217,255,.08);backdrop-filter:blur(16px)}
.block-container{max-width:1520px;padding:28px 36px 70px}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;color:var(--text)!important}
p,label,span,.stMarkdown{color:var(--text)}
[data-testid="stSidebar"],[data-testid="stSidebar"]>div{background:#07111f!important;border-right:1px solid var(--line)!important}
[data-testid="stSidebar"] *{color:var(--text)!important}
[data-testid="stSidebar"] .stCaption{color:var(--muted)!important}
[data-testid="stSidebar"] .stButton button{background:#0b1628!important;border:1px solid rgba(0,217,255,.18)!important;color:var(--text)!important}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px}
.brand{font:700 1.35rem 'Space Grotesk';letter-spacing:-.04em}.brand b{color:var(--cyan)}
.live{border:1px solid rgba(53,208,127,.3);background:rgba(53,208,127,.08);border-radius:999px;padding:7px 11px;font-size:.68rem;font-weight:700;color:var(--green)!important;letter-spacing:.08em;text-transform:uppercase}
.hero{position:relative;overflow:hidden;border:1px solid rgba(0,217,255,.16);border-radius:16px;padding:38px;background:linear-gradient(135deg,rgba(11,22,40,.96),rgba(7,17,31,.98));box-shadow:0 16px 40px rgba(0,4,15,.65),0 0 40px rgba(0,217,255,.04)}
.hero:after{content:"";position:absolute;width:420px;height:420px;right:-180px;top:-220px;border-radius:50%;background:rgba(0,217,255,.07);filter:blur(90px)}
.eyebrow{font:700 .68rem 'Space Grotesk';letter-spacing:.16em;color:var(--cyan)!important;text-transform:uppercase}
.hero h1{font-size:clamp(2.7rem,5vw,5rem);line-height:.95;letter-spacing:-.07em;margin:13px 0 15px;position:relative;z-index:1}.hero h1 span{color:var(--cyan);text-shadow:0 0 28px rgba(0,217,255,.18)}
.hero p{max-width:820px;color:var(--muted)!important;font-size:1rem;line-height:1.65;position:relative;z-index:1}
.card,.metric{background:rgba(11,22,40,.88);border:1px solid rgba(0,217,255,.12);border-radius:12px;padding:20px;box-shadow:0 16px 40px rgba(0,4,15,.45)}
.action{border-color:rgba(0,217,255,.25)!important;background:linear-gradient(135deg,rgba(11,22,40,.96),rgba(13,27,48,.9))!important}
.metric{padding:16px 18px}.metric small{display:block;color:var(--steel)!important;text-transform:uppercase;letter-spacing:.12em;font:700 .64rem 'Space Grotesk'}.metric strong{display:block;font:700 2rem 'Space Grotesk';margin-top:6px}.safe strong{color:var(--green)}.flag strong{color:var(--red)}.review strong{color:var(--amber)}.score strong{color:var(--cyan)}
.badge{display:inline-block;border:1px solid rgba(0,217,255,.2);border-radius:999px;padding:5px 9px;font:700 .68rem 'Space Grotesk';background:rgba(13,27,48,.8);letter-spacing:.06em}.clean{color:var(--green)!important}.exception{color:var(--red)!important}.human{color:var(--amber)!important}
div.stButton>button,div.stDownloadButton>button{min-height:44px!important;border-radius:10px!important;border:1px solid rgba(0,217,255,.22)!important;background:#0b1628!important;color:var(--text)!important;font:600 14px 'Space Grotesk'!important;box-shadow:none!important}
div.stButton>button:hover,div.stDownloadButton>button:hover{border-color:var(--cyan)!important;background:#0d1b30!important;transform:translateY(-1px)!important;box-shadow:0 0 24px rgba(0,217,255,.10)!important}
button[kind="primary"]{background:linear-gradient(135deg,#00d9ff,#147bff)!important;color:#04101c!important;border:0!important;box-shadow:0 0 20px rgba(0,217,255,.28),0 4px 12px rgba(0,0,0,.5)!important}
[data-testid="stFileUploader"],[data-testid="stFileUploader"] section{background:#0b1628!important;border:1px dashed rgba(0,217,255,.28)!important;border-radius:12px!important}
[data-testid="stFileUploader"] button{background:#0d1b30!important;color:var(--text)!important;border:1px solid rgba(0,217,255,.2)!important}
.stTextInput>div>div,.stTextArea>div>div,.stSelectbox>div>div,input,textarea,[data-baseweb="select"]>div{background:#07111f!important;color:var(--text)!important;border-color:rgba(0,217,255,.18)!important}
[data-testid="stDataFrame"],[data-testid="stDataFrame"]>div{background:#0b1628!important;border:1px solid rgba(0,217,255,.12)!important;border-radius:10px!important;overflow:hidden}
[data-testid="stTabs"] [role="tab"]{font:700 12px 'Space Grotesk';letter-spacing:.05em;color:var(--steel)!important}.stTabs [aria-selected="true"]{color:var(--cyan)!important}
[data-testid="stChatMessage"]{background:#0b1628!important;border:1px solid rgba(0,217,255,.12)!important;border-radius:12px}
[data-testid="stChatInput"]{background:#0b1628!important;border-color:rgba(0,217,255,.18)!important}
[data-testid="stExpander"]{background:#0b1628!important;border:1px solid rgba(0,217,255,.12)!important;border-radius:10px}
.stAlert{background:#0b1628!important;color:var(--text)!important;border:1px solid rgba(0,217,255,.14)!important}
.muted{color:var(--muted)!important}.footer{text-align:center;color:var(--steel)!important;font:700 .62rem 'Space Grotesk';letter-spacing:.16em;margin-top:44px}
[data-testid="stMetricValue"]{color:var(--text)!important;font-family:'Space Grotesk'!important}
hr{border-color:var(--line)!important}
code{background:#04101c!important;color:#9deeff!important}
@media(max-width:800px){.block-container{padding:18px 12px 50px}.hero{padding:25px}.hero h1{font-size:3.3rem}}
</style>
""",
    unsafe_allow_html=True,
)


def init_state():
    defaults = {
        "df": None, "source_name": "", "results": [], "analyzed": False,
        "audit": [], "reviews": {}, "chat": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_workspace(df=None, source_name=""):
    st.session_state.df = df
    st.session_state.source_name = source_name
    st.session_state.results = []
    st.session_state.analyzed = False
    st.session_state.audit = []
    st.session_state.reviews = {}
    st.session_state.chat = []


def load_sample():
    return pd.read_csv(ROOT / "data" / "invoices.csv")


def add_audit(event, invoice_id="", message="", metadata=None):
    record = {
        "timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "event": event,
        "invoice_id": str(invoice_id),
        "message": message,
    }
    st.session_state.audit.append(record)
    try:
        from src.persistence import save_audit_event
        save_audit_event(event, invoice_id, message, metadata)
    except Exception:
        pass


def build_results_df(results):
    return pd.DataFrame([
        {
            "invoice_id": r.get("invoice_id"),
            "vendor": (r.get("evidence") or {}).get("vendor"),
            "amount": (r.get("evidence") or {}).get("amount"),
            "category": (r.get("evidence") or {}).get("category"),
            "invoice_date": (r.get("evidence") or {}).get("invoice_date"),
            "status": r.get("status"),
            "route": r.get("route"),
            "confidence": float(r.get("confidence", 0)),
            "human_review_required": bool(r.get("human_review_required")),
            "rule_ids": ", ".join(r.get("rule_ids") or []),
            "reasons": " | ".join(str(x.get("message", "")) for x in r.get("reasons", [])),
            "matched_invoice_id": (r.get("evidence") or {}).get("matched_invoice_id"),
        }
        for r in results
    ])


def run_analysis():
    if st.session_state.df is None:
        st.warning("Load or upload an invoice CSV first.")
        return
    try:
        results = process_invoices(st.session_state.df)
        st.session_state.results = results
        st.session_state.analyzed = True
        summary = summarize_results(results)
        add_audit(
            "ANALYSIS_RUN", "", 
            f"{st.session_state.source_name}: {summary['total']} invoices analyzed.",
            {"summary": summary},
        )
        for result in results:
            add_audit(
                "DECISION",
                result.get("invoice_id", ""),
                f"{result.get('status')} / {result.get('route')}",
                {"rule_ids": result.get("rule_ids", []), "confidence": result.get("confidence")},
            )
        st.toast(f"Analysis complete · {summary['total']} invoices", icon="✨")
    except Exception as exc:
        st.session_state.analyzed = False
        st.error(f"Analysis failed: {exc}")


def metrics(results):
    summary = summarize_results(results)
    average = sum(float(r.get("confidence", 0)) for r in results) / len(results) if results else 0
    values = [
        ("Invoices", summary["total"], ""),
        ("Auto-pass", summary["clean"], "safe"),
        ("Exceptions", summary["exceptions"], "flag"),
        ("Human review", summary["review_required"], "review"),
        ("Confidence", f"{average:.0%}", "score"),
    ]
    cols = st.columns(5)
    for col, (label, value, kind) in zip(cols, values):
        with col:
            st.markdown(f'<div class="metric {kind}"><small>{label}</small><strong>{value}</strong></div>', unsafe_allow_html=True)


def render_results():
    results = st.session_state.results
    if not results:
        return

    metrics(results)
    out = build_results_df(results)
    st.markdown("### DECISION RESULTS")
    st.dataframe(
        out[["invoice_id","vendor","amount","category","status","route","confidence","human_review_required"]],
        width="stretch",
        hide_index=True,
        column_config={
            "confidence": st.column_config.ProgressColumn(
                "Confidence", min_value=0, max_value=1, format="%.0f%%"
            )
        },
    )

    exceptions = out[out.status == "EXCEPTION"].copy()
    if not exceptions.empty:
        st.markdown("### EXCEPTIONS")
        st.dataframe(
            exceptions[["invoice_id","vendor","amount","category","rule_ids","reasons","route"]],
            width="stretch",
            hide_index=True,
        )

    a, b, c = st.columns(3)
    with a:
        st.download_button(
            "↓ Download analyzed CSV",
            out.to_csv(index=False).encode(),
            "finsight_analyzed.csv",
            "text/csv",
            width="stretch",
        )
    with b:
        st.download_button(
            f"↓ Download exceptions ({len(exceptions)})",
            exceptions.to_csv(index=False).encode(),
            "finsight_exceptions.csv",
            "text/csv",
            width="stretch",
        )
    with c:
        st.download_button(
            "↓ Download original CSV",
            st.session_state.df.to_csv(index=False).encode(),
            "finsight_original.csv",
            "text/csv",
            width="stretch",
        )


def review_tab():
    items = [r for r in st.session_state.results if r.get("human_review_required")]
    if not items:
        st.success("No invoices currently require human review.")
        return
    st.info(f"{len(items)} invoice(s) require a human decision. AI cannot approve or reject them.")
    for result in items:
        iid = str(result.get("invoice_id"))
        old = st.session_state.reviews.get(iid, {})
        with st.container(border=True):
            st.markdown(f"#### {iid}")
            reasons = " ".join(str(x.get("message", "")) for x in result.get("reasons", []))
            st.write(reasons or "Review required.")
            st.caption(f"Route: {result.get('route')} · Confidence: {float(result.get('confidence', 0)):.0%}")
            with st.expander("Evidence"):
                st.json({
                    "evidence": result.get("evidence"),
                    "rule_ids": result.get("rule_ids"),
                    "reasons": result.get("reasons"),
                })
            note = st.text_area("Reviewer note", value=old.get("comment", ""), key=f"review_note_{iid}")
            left, right = st.columns(2)
            with left:
                if st.button("Approve", key=f"approve_{iid}", width="stretch"):
                    st.session_state.reviews[iid] = {"action":"APPROVED","comment":note.strip()}
                    add_audit("REVIEW_ACTION", iid, f"APPROVED: {note.strip()}")
                    st.success(f"{iid} marked APPROVED.")
            with right:
                if st.button("Reject", key=f"reject_{iid}", width="stretch"):
                    st.session_state.reviews[iid] = {"action":"REJECTED","comment":note.strip()}
                    add_audit("REVIEW_ACTION", iid, f"REJECTED: {note.strip()}")
                    st.warning(f"{iid} marked REJECTED.")


def evidence_tab():
    ids = [str(r.get("invoice_id")) for r in st.session_state.results]
    selected = st.selectbox("Select invoice", ids, key="evidence_invoice")
    result = next(r for r in st.session_state.results if str(r.get("invoice_id")) == selected)
    badge_class = "clean" if result.get("status") == "CLEAN" else "exception"
    st.markdown(
        f'<span class="badge {badge_class}">● {result.get("status")}</span> '
        f'<span class="badge">{result.get("route")}</span>',
        unsafe_allow_html=True,
    )
    a, b, c = st.columns(3)
    a.metric("Confidence", f"{float(result.get('confidence', 0)):.0%}")
    b.metric("Rule flags", len(result.get("rule_ids") or []))
    c.metric("Human review", "Required" if result.get("human_review_required") else "Not required")
    st.markdown("### Why this happened")
    if not result.get("reasons"):
        st.success("No rule violations. This invoice passed all configured checks.")
    else:
        for reason in result["reasons"]:
            with st.expander(f"{reason.get('rule')} · {reason.get('message')}", expanded=True):
                st.write("Actual:", reason.get("actual_value"))
                st.write("Expected:", reason.get("expected_value"))
                if reason.get("matched_invoice_id"):
                    st.write("Matched invoice:", reason.get("matched_invoice_id"))
    st.markdown("### Trusted evidence")
    st.json(result.get("evidence") or {})


def copilot_tab():
    st.markdown("Ask FinSight about the loaded analysis. It is intentionally limited to FinSight, invoice, AP, audit, rule-engine, CSV, and application questions.")
    if not st.session_state.results:
        st.info("Analyze the CSV first for invoice-specific Copilot answers.")
    prompts = [
        "Summarize this batch",
        "Which invoices need review?",
        "Explain every exception",
        "Why is INV003 flagged?",
    ]
    cols = st.columns(4)
    for col, prompt in zip(cols, prompts):
        with col:
            if st.button(prompt, key="quick_" + prompt, width="stretch"):
                from src.copilot_workflow import copilot_workflow
                st.session_state.chat.append(("user", prompt))
                response = copilot_workflow(prompt, st.session_state.results, st.session_state.chat[:-1])
                st.session_state.chat.append(("assistant", response["answer"], response["mode"]))
                st.rerun()

    for item in st.session_state.chat:
        with st.chat_message(item[0]):
            st.markdown(item[1])
            if len(item) > 2:
                st.caption(f"Source: {item[2]}")

    question = st.chat_input("Ask FinSight…")
    if question:
        from src.copilot_workflow import copilot_workflow
        st.session_state.chat.append(("user", question))
        response = copilot_workflow(question, st.session_state.results, st.session_state.chat[:-1])
        st.session_state.chat.append(("assistant", response["answer"], response["mode"]))
        st.rerun()


def main():
    init_state()

    with st.sidebar:
        st.markdown("## ✦ FinSight")
        st.caption("Accounts-payable intelligence")
        st.markdown('<span class="live">● RULE ENGINE ONLINE</span>', unsafe_allow_html=True)
        st.divider()
        st.markdown("**Required CSV columns**")
        st.code("\n".join(REQUIRED_COLUMNS), language="text")
        st.markdown("**Configured limits**")
        for category, limit in CATEGORY_LIMITS.items():
            st.caption(f"{category} · ₹{limit:,.0f}")

        st.divider()
        if st.button("Log out", key="logout", width="stretch"):
            st.session_state.authenticated = False
            st.session_state.login_error = ""
            st.rerun()

    st.markdown(
        f'<div class="top"><div class="brand">FINSIGHT <b>/ AP INTELLIGENCE</b></div>'
        f'<div class="live">● {st.session_state.source_name or "NO DATASET LOADED"}</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero"><div class="eyebrow">INVOICE INTELLIGENCE · EVIDENCE · HUMAN REVIEW</div>'
        '<h1>Analyze every invoice.<br><span>See every decision.</span></h1>'
        '<p>Upload a CSV, run the deterministic rule engine, inspect the exact evidence behind each result, and send uncertain cases to human review.</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown("### 01 · LOAD INVOICE DATA")
    upload_col, sample_col, reset_col = st.columns([5, 1.5, 1.2])
    with upload_col:
        uploaded = st.file_uploader(
            "Invoice CSV",
            type=["csv"],
            key="invoice_upload",
            help="Required: invoice_id, vendor, amount, category, invoice_date",
        )
    with sample_col:
        st.write("")
        st.write("")
        if st.button("Load sample", key="load_sample", width="stretch"):
            reset_workspace(load_sample(), "data/invoices.csv")
            st.rerun()
    with reset_col:
        st.write("")
        st.write("")
        if st.button("Reset", key="reset_workspace", width="stretch"):
            reset_workspace()
            st.rerun()

    if uploaded is not None and uploaded.name != st.session_state.source_name:
        try:
            reset_workspace(pd.read_csv(uploaded), uploaded.name)
            st.toast(f"{uploaded.name} loaded", icon="✨")
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")

    if st.session_state.df is None:
        st.markdown(
            '<div class="card action"><h3>Nothing loaded yet</h3>'
            '<p class="muted">Load the bundled sample or upload your own CSV. The Analyze button will appear here as soon as data is ready.</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown("### What FinSight checks")
        a,b,c,d = st.columns(4)
        for col, num, title, body in [
            (a,"01","Schema","Required fields, missing values, dates and amounts."),
            (b,"02","Rules","Category limits, invalid values and duplicate invoices."),
            (c,"03","Review","Uncertain exceptions are routed to a human."),
            (d,"04","Evidence","Every decision includes rule IDs and matched records."),
        ]:
            with col:
                st.markdown(f'<div class="card"><b>{num}</b><h4>{title}</h4><p class="muted">{body}</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="footer">FINSIGHT · DETERMINISTIC DECISIONS · HUMAN JUDGMENT</div>', unsafe_allow_html=True)
        return

    df = st.session_state.df
    st.markdown("### 02 · RUN DETERMINISTIC ANALYSIS")
    left, right = st.columns([4, 1.5])
    with left:
        st.markdown(
            f'<div class="card"><b>{st.session_state.source_name}</b><br>'
            f'<span class="muted">{len(df):,} invoice rows loaded · {len(df.columns)} columns · required schema checked when analysis runs</span></div>',
            unsafe_allow_html=True,
        )
    with right:
        if st.button("✦ ANALYZE INVOICES", key="analyze_btn", type="primary", width="stretch"):
            run_analysis()
            st.rerun()

    st.markdown("### SOURCE PREVIEW")
    st.dataframe(df.head(100), width="stretch", hide_index=True)

    if not st.session_state.analyzed:
        st.markdown(
            '<div class="card action"><h3>Ready to analyze</h3>'
            '<p class="muted">Press <b>ANALYZE INVOICES</b> above. Results will appear directly below — no separate page or hidden navigation required.</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="footer">FINSIGHT · READY FOR ANALYSIS</div>', unsafe_allow_html=True)
        return

    st.markdown("### 03 · ANALYSIS RESULTS")
    render_results()

    tabs = st.tabs(["Review queue", "Evidence", "Copilot", "Audit & system"])
    with tabs[0]:
        review_tab()
    with tabs[1]:
        evidence_tab()
    with tabs[2]:
        copilot_tab()
    with tabs[3]:
        st.markdown("#### Session audit")
        if st.session_state.audit:
            st.dataframe(pd.DataFrame(st.session_state.audit), width="stretch", hide_index=True)
        else:
            st.info("No audit events in this session.")
        st.markdown("#### Configuration")
        st.write({"required_columns": REQUIRED_COLUMNS, "category_limits": CATEGORY_LIMITS})
        try:
            from src.ai import test_gemini_connection
            ok, msg = test_gemini_connection()
            st.write({"Gemini": "Connected" if ok else "Not connected", "message": msg})
        except Exception as exc:
            st.write({"Gemini": "Not connected", "message": str(exc)})

    st.markdown('<div class="footer">FINSIGHT · PYTHON RULE ENGINE IS THE SOURCE OF TRUTH · AI EXPLAINS, NEVER DECIDES</div>', unsafe_allow_html=True)


if require_login():
    main()
