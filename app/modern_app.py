"""FinSight AI-first Streamlit workspace.

UI layers:
- deterministic policy validation
- supervised trained risk model
- neural anomaly detection
- human review
- evidence and audit trail
- FinSight Copilot
"""
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


st.set_page_config(
    page_title="FinSight · AP Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#f5f7fb;--card:#fff;--line:#e3e7ef;--text:#151927;--muted:#667085;--violet:#6947f5;--pink:#e44791;--cyan:#0b9db9;--green:#168a62;--amber:#a96b00;--red:#d13a59}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:linear-gradient(180deg,#fbfcff 0%,#f3f6fb 100%)!important;color:var(--text)!important}
body,[class*="css"]{font-family:'DM Sans',sans-serif}
[data-testid="stHeader"]{background:rgba(255,255,255,.9)!important;border-bottom:1px solid var(--line)}
.block-container{max-width:1500px;padding:24px 34px 70px}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;color:var(--text)!important}
p,label,span,.stMarkdown{color:var(--text)}
[data-testid="stSidebar"],[data-testid="stSidebar"]>div{background:#fff!important;border-right:1px solid var(--line)!important}
[data-testid="stSidebar"] *{color:var(--text)!important}
[data-testid="stSidebar"] .stCaption{color:var(--muted)!important}
.header{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}
.logo{font:700 1.25rem 'Space Grotesk';letter-spacing:-.04em}.logo span{color:var(--violet)}
.pill{display:inline-flex;align-items:center;gap:7px;border:1px solid #dfe5ee;background:#fff;border-radius:999px;padding:7px 11px;font-size:.68rem;font-weight:800}
.dot{width:7px;height:7px;border-radius:50%;background:var(--green);display:inline-block}
.hero{border:1px solid #dfe3ed;border-radius:28px;padding:34px 38px;background:radial-gradient(circle at 92% 0%,rgba(105,71,245,.17),transparent 32%),radial-gradient(circle at 70% 100%,rgba(11,157,185,.09),transparent 25%),linear-gradient(135deg,#fff,#f8f5ff 72%,#f2fcff);box-shadow:0 20px 60px rgba(38,43,70,.07)}
.eyebrow{font-size:.65rem;font-weight:800;letter-spacing:.2em;color:#6947f5!important}
.hero h1{font-size:clamp(2.5rem,5vw,5rem);line-height:.93;letter-spacing:-.07em;margin:12px 0}
.gradient{background:linear-gradient(90deg,var(--pink),var(--violet),var(--cyan));-webkit-background-clip:text;color:transparent}
.hero p{max-width:820px;color:#5d6678!important;line-height:1.65}
.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:0 8px 30px rgba(38,43,70,.045)}
.section{margin-top:28px}
.metric{background:#fff;border:1px solid var(--line);border-radius:17px;padding:15px 17px;min-height:90px;box-shadow:0 7px 22px rgba(38,43,70,.04)}
.metric small{display:block;color:var(--muted)!important;text-transform:uppercase;letter-spacing:.1em;font-size:.61rem;font-weight:700}
.metric strong{display:block;font:700 1.9rem 'Space Grotesk';margin-top:7px}
.metric.safe strong{color:var(--green)}.metric.flag strong{color:var(--red)}.metric.review strong{color:var(--amber)}.metric.ai strong{color:var(--violet)}.metric.dl strong{color:var(--cyan)}
.engine{display:flex;gap:9px;flex-wrap:wrap;margin:12px 0}
.engine span{padding:7px 10px;border:1px solid var(--line);background:#fafbfe;border-radius:10px;font-size:.68rem;font-weight:800}
.engine .active{background:#f4f1ff;border-color:#d8ceff;color:#6040dc!important}
.engine .human{background:#fff8e9;border-color:#f0dca8;color:#9a6400!important}
.badge{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:5px 9px;font-size:.65rem;font-weight:800;background:#fff}
.clean{color:var(--green)!important}.exception{color:var(--red)!important}.human{color:var(--amber)!important}.ai{color:var(--violet)!important}
div.stButton>button,div.stDownloadButton>button{min-height:43px!important;border-radius:11px!important;border:1px solid #dfe3eb!important;background:#fff!important;color:#222737!important;font-weight:700!important;box-shadow:0 4px 12px rgba(30,35,60,.035)!important}
div.stButton>button:hover,div.stDownloadButton>button:hover{border-color:#bdb0ff!important;transform:translateY(-1px)!important}
button[kind="primary"]{background:linear-gradient(100deg,#e44791,#6947f5)!important;color:#fff!important;border:0!important;box-shadow:0 12px 28px rgba(105,71,245,.18)!important}
[data-testid="stFileUploader"],[data-testid="stFileUploader"] section{background:#fff!important;border:1px dashed #cbd2df!important;border-radius:15px!important}
[data-testid="stFileUploader"] button{background:#f7f8fc!important;color:#222737!important;border:1px solid #dfe3eb!important}
.stTextInput>div>div,.stTextArea>div>div,.stSelectbox>div>div,input,textarea,[data-baseweb="select"]>div{background:#fff!important;color:#1b2030!important;border-color:#d9dee8!important}
[data-testid="stDataFrame"],[data-testid="stDataFrame"]>div{background:#fff!important;border:1px solid var(--line)!important;border-radius:14px!important;overflow:hidden}
[data-testid="stTabs"] [role="tab"]{font-weight:700;color:#667085!important}
[data-testid="stTabs"] [aria-selected="true"]{color:#6947f5!important}
[data-testid="stChatMessage"]{background:#fff!important;border:1px solid var(--line)!important;border-radius:15px!important}
[data-testid="stChatInput"]{background:#fff!important;border-color:#d9dee8!important}
[data-testid="stExpander"]{background:#fff!important;border:1px solid var(--line)!important;border-radius:13px!important}
.stAlert{background:#fff!important;color:#1b2030!important;border:1px solid var(--line)!important}
.muted{color:var(--muted)!important}.footer{text-align:center;color:#939aaa!important;font-size:.61rem;letter-spacing:.15em;margin-top:42px}
@media(max-width:800px){.block-container{padding:16px 12px 50px}.hero{padding:25px}.hero h1{font-size:3.2rem}}
</style>
""",
    unsafe_allow_html=True,
)


def init_state():
    defaults = {
        "df": None,
        "source_name": "",
        "results": [],
        "analyzed": False,
        "audit": [],
        "reviews": {},
        "chat": [],
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


def model_state(results):
    trained = any(bool(r.get("ai_available")) for r in results)
    neural = any(bool(r.get("dl_available")) for r in results)
    return trained, neural


def build_results_df(results):
    rows = []
    for r in results:
        evidence = r.get("evidence") or {}
        rows.append({
            "invoice_id": r.get("invoice_id"),
            "vendor": evidence.get("vendor"),
            "amount": evidence.get("amount"),
            "category": evidence.get("category"),
            "status": r.get("status"),
            "route": r.get("route"),
            "AI risk": float(r.get("ai_risk_score", 0)),
            "DL anomaly": float(r.get("dl_anomaly_score", 0)),
            "Hybrid risk": float(r.get("hybrid_risk_score", 0)),
            "confidence": float(r.get("confidence", 0)),
            "human_review_required": bool(r.get("human_review_required")),
            "rule_ids": ", ".join(r.get("rule_ids") or []),
            "reasons": " | ".join(str(x.get("message", "")) for x in r.get("reasons", [])),
            "matched_invoice_id": evidence.get("matched_invoice_id"),
        })
    return pd.DataFrame(rows)


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
            "ANALYSIS_RUN",
            "",
            f"{st.session_state.source_name}: {summary['total']} invoices analyzed.",
            {"summary": summary},
        )
        for result in results:
            add_audit(
                "DECISION",
                result.get("invoice_id", ""),
                f"{result.get('status')} / {result.get('route')}",
                {
                    "rule_ids": result.get("rule_ids", []),
                    "confidence": result.get("confidence"),
                    "ai_risk": result.get("ai_risk_score", 0),
                    "dl_anomaly": result.get("dl_anomaly_score", 0),
                    "hybrid_risk": result.get("hybrid_risk_score", 0),
                },
            )
        st.toast(f"Analysis complete · {summary['total']} invoices", icon="✦")
    except Exception as exc:
        st.session_state.analyzed = False
        st.error(f"Analysis failed: {exc}")


def render_metrics(results):
    summary = summarize_results(results)
    trained, neural = model_state(results)
    values = [
        ("Invoices", summary["total"], ""),
        ("Auto-pass", summary["clean"], "safe"),
        ("Exceptions", summary["exceptions"], "flag"),
        ("Human review", summary["review_required"], "review"),
        ("ML model", "ON" if trained else "OFF", "ai"),
        ("Deep learning", "ON" if neural else "OFF", "dl"),
    ]
    cols = st.columns(6)
    for col, (label, value, kind) in zip(cols, values):
        with col:
            st.markdown(
                f'<div class="metric {kind}"><small>{label}</small><strong>{value}</strong></div>',
                unsafe_allow_html=True,
            )


def render_ai_overview(results):
    trained, neural = model_state(results)
    avg_ai = sum(float(r.get("ai_risk_score", 0)) for r in results) / len(results) if results else 0
    avg_dl = sum(float(r.get("dl_anomaly_score", 0)) for r in results) / len(results) if results else 0
    avg_hybrid = sum(float(r.get("hybrid_risk_score", 0)) for r in results) / len(results) if results else 0

    st.markdown("#### Hybrid intelligence")
    st.markdown(
        '<div class="engine">'
        '<span class="active">01 · POLICY RULES</span>'
        f'<span class="{"active" if trained else ""}">02 · TRAINED ML</span>'
        f'<span class="{"active" if neural else ""}">03 · NEURAL ANOMALY</span>'
        '<span class="human">04 · HUMAN REVIEW</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    with cols[0]:
        st.metric("Average ML risk", f"{avg_ai:.0%}", help="Supervised model risk estimate.")
    with cols[1]:
        st.metric("Average anomaly", f"{avg_dl:.0%}", help="Neural autoencoder anomaly score.")
    with cols[2]:
        st.metric("Average hybrid risk", f"{avg_hybrid:.0%}", help="Combined advisory signal.")
    if trained or neural:
        st.caption("AI signals are advisory. Deterministic policy rules remain the source of truth; uncertain cases can be sent to human review.")
    else:
        st.warning("AI models are not loaded for this session. Deterministic invoice checks are still fully active.")


def render_results():
    results = st.session_state.results
    if not results:
        return

    render_metrics(results)
    render_ai_overview(results)

    out = build_results_df(results)
    st.markdown("### Decision results")
    display = out[
        [
            "invoice_id", "vendor", "amount", "category", "status", "route",
            "AI risk", "DL anomaly", "Hybrid risk", "confidence",
            "human_review_required",
        ]
    ].copy()
    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        column_config={
            "AI risk": st.column_config.ProgressColumn("ML risk", min_value=0, max_value=1, format="%.0f%%"),
            "DL anomaly": st.column_config.ProgressColumn("DL anomaly", min_value=0, max_value=1, format="%.0f%%"),
            "Hybrid risk": st.column_config.ProgressColumn("Hybrid risk", min_value=0, max_value=1, format="%.0f%%"),
            "confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1, format="%.0f%%"),
        },
    )

    exceptions = out[out.status == "EXCEPTION"].copy()
    if not exceptions.empty:
        st.markdown("### Exception intelligence")
        st.dataframe(
            exceptions[
                ["invoice_id", "vendor", "amount", "category", "rule_ids", "reasons", "route"]
            ],
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
            st.caption(
                f"Route: {result.get('route')} · "
                f"ML risk: {float(result.get('ai_risk_score', 0)):.0%} · "
                f"DL anomaly: {float(result.get('dl_anomaly_score', 0)):.0%} · "
                f"Hybrid: {float(result.get('hybrid_risk_score', 0)):.0%}"
            )
            with st.expander("Decision evidence"):
                st.json({
                    "evidence": result.get("evidence"),
                    "rule_ids": result.get("rule_ids"),
                    "reasons": result.get("reasons"),
                    "ai": {
                        "risk_score": result.get("ai_risk_score"),
                        "status": result.get("ai_risk_status"),
                        "reason": result.get("ai_reason"),
                    },
                    "deep_learning": {
                        "anomaly_score": result.get("dl_anomaly_score"),
                        "status": result.get("dl_status"),
                        "reason": result.get("dl_reason"),
                    },
                })
            note = st.text_area("Reviewer note", value=old.get("comment", ""), key=f"review_note_{iid}")
            left, right = st.columns(2)
            with left:
                if st.button("Approve", key=f"approve_{iid}", width="stretch"):
                    st.session_state.reviews[iid] = {"action": "APPROVED", "comment": note.strip()}
                    add_audit("REVIEW_ACTION", iid, f"APPROVED: {note.strip()}")
                    st.success(f"{iid} marked APPROVED.")
            with right:
                if st.button("Reject", key=f"reject_{iid}", width="stretch"):
                    st.session_state.reviews[iid] = {"action": "REJECTED", "comment": note.strip()}
                    add_audit("REVIEW_ACTION", iid, f"REJECTED: {note.strip()}")
                    st.warning(f"{iid} marked REJECTED.")


def evidence_tab():
    if not st.session_state.results:
        st.info("Analyze a dataset first.")
        return
    ids = [str(r.get("invoice_id")) for r in st.session_state.results]
    selected = st.selectbox("Select invoice", ids, key="evidence_invoice")
    result = next(r for r in st.session_state.results if str(r.get("invoice_id")) == selected)
    status_class = "clean" if result.get("status") == "CLEAN" else "exception"

    st.markdown(
        f'<span class="badge {status_class}">● {result.get("status")}</span> '
        f'<span class="badge">{result.get("route")}</span> '
        f'<span class="badge ai">HYBRID {float(result.get("hybrid_risk_score", 0)):.0%}</span>',
        unsafe_allow_html=True,
    )

    cols = st.columns(5)
    cols[0].metric("Confidence", f"{float(result.get('confidence', 0)):.0%}")
    cols[1].metric("ML risk", f"{float(result.get('ai_risk_score', 0)):.0%}")
    cols[2].metric("DL anomaly", f"{float(result.get('dl_anomaly_score', 0)):.0%}")
    cols[3].metric("Hybrid risk", f"{float(result.get('hybrid_risk_score', 0)):.0%}")
    cols[4].metric("Human review", "Required" if result.get("human_review_required") else "Not required")

    st.markdown("### Why FinSight reached this result")
    if not result.get("reasons"):
        st.success("No deterministic rule violations were found.")
    else:
        for reason in result["reasons"]:
            with st.expander(f"{reason.get('rule')} · {reason.get('message')}", expanded=True):
                st.write("Actual:", reason.get("actual_value"))
                st.write("Expected:", reason.get("expected_value"))
                if reason.get("matched_invoice_id"):
                    st.write("Matched invoice:", reason.get("matched_invoice_id"))

    st.markdown("### AI reasoning signals")
    ai_col, dl_col = st.columns(2)
    with ai_col:
        st.markdown('<div class="card"><b>Supervised ML</b></div>', unsafe_allow_html=True)
        st.write(result.get("ai_reason", "Model unavailable."))
        st.progress(float(result.get("ai_risk_score", 0)))
    with dl_col:
        st.markdown('<div class="card"><b>Neural anomaly detector</b></div>', unsafe_allow_html=True)
        st.write(result.get("dl_reason", "Detector unavailable."))
        st.progress(float(result.get("dl_anomaly_score", 0)))

    st.markdown("### Trusted evidence")
    st.json(result.get("evidence") or {})


def copilot_tab():
    st.markdown(
        "FinSight Copilot answers questions about the current invoice analysis, "
        "rules, evidence, review queue, audit trail, and application. It is not a general-purpose chatbot."
    )
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

    question = st.chat_input("Ask FinSight about this analysis…")
    if question:
        from src.copilot_workflow import copilot_workflow
        st.session_state.chat.append(("user", question))
        response = copilot_workflow(question, st.session_state.results, st.session_state.chat[:-1])
        st.session_state.chat.append(("assistant", response["answer"], response["mode"]))
        st.rerun()


def system_tab():
    trained = False
    model_meta = {}
    try:
        from src.trained_ai import DEFAULT_MODEL_PATH
        trained = DEFAULT_MODEL_PATH.exists()
        meta_path = DEFAULT_MODEL_PATH.with_suffix(".json")
        if meta_path.exists():
            import json
            model_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        pass

    st.markdown("#### System status")
    cols = st.columns(4)
    cols[0].metric("Policy engine", "ONLINE")
    cols[1].metric("Trained ML", "READY" if trained else "NOT LOADED")
    cols[2].metric("Deep learning", "BATCH MODE")
    cols[3].metric("Copilot", "CONFIGURED")

    st.markdown("#### Model metadata")
    if model_meta:
        st.json(model_meta)
    else:
        st.info("No persisted trained model artifact is bundled yet. The deterministic engine remains fully operational.")

    st.markdown("#### Configuration")
    st.json({
        "required_columns": REQUIRED_COLUMNS,
        "category_limits": CATEGORY_LIMITS,
        "ai_policy": "Advisory only; deterministic rules remain authoritative.",
        "human_review": "Required for rule exceptions and AI-routed uncertainty.",
    })

    st.markdown("#### Session audit")
    if st.session_state.audit:
        st.dataframe(pd.DataFrame(st.session_state.audit), width="stretch", hide_index=True)
    else:
        st.info("No audit events in this session.")


def main():
    init_state()

    with st.sidebar:
        st.markdown("## ✦ FinSight")
        st.caption("Accounts-payable intelligence workspace")
        st.markdown('<span class="pill"><span class="dot"></span> POLICY ENGINE ONLINE</span>', unsafe_allow_html=True)
        st.divider()
        st.markdown("**Hybrid pipeline**")
        for item in ["Policy rules", "Trained ML", "Neural anomaly detection", "Human review"]:
            st.caption("✓ " + item)
        st.divider()
        st.markdown("**Required CSV columns**")
        st.code("\n".join(REQUIRED_COLUMNS), language="text")
        st.markdown("**Category limits**")
        for category, limit in CATEGORY_LIMITS.items():
            st.caption(f"{category} · ₹{limit:,.0f}")

    st.markdown(
        f'<div class="header"><div class="logo">FINSIGHT <span>/ AP INTELLIGENCE</span></div>'
        f'<div class="pill"><span class="dot"></span> {st.session_state.source_name or "NO DATASET LOADED"}</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero"><div class="eyebrow">POLICY · MACHINE LEARNING · ANOMALIES · HUMAN JUDGMENT</div>'
        '<h1>Invoice intelligence,<br><span class="gradient">without black-box decisions.</span></h1>'
        '<p>Upload invoices, validate them against configured AP policy, score learned risk, detect unusual patterns with a neural autoencoder, and send uncertain cases to a human reviewer with the evidence attached.</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section"><h3>1 · Load invoice data</h3></div>', unsafe_allow_html=True)
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
            st.toast(f"{uploaded.name} loaded", icon="✦")
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")

    if st.session_state.df is None:
        st.markdown(
            '<div class="card"><h3>Ready for your first analysis</h3>'
            '<p class="muted">Load the sample or upload your CSV. FinSight will validate the schema before running the decision pipeline.</p></div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(4)
        cards = [
            ("01", "Validate", "Required fields, dates, amounts and schema."),
            ("02", "Learn", "Supervised risk model plus neural anomaly detection."),
            ("03", "Review", "Exceptions and uncertain cases go to a human."),
            ("04", "Explain", "Evidence, rule IDs, model signals and audit events."),
        ]
        for col, (num, title, body) in zip(cols, cards):
            with col:
                st.markdown(f'<div class="card"><b>{num}</b><h4>{title}</h4><p class="muted">{body}</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="footer">FINSIGHT · POLICY FIRST · AI ASSISTED · HUMAN CONTROL</div>', unsafe_allow_html=True)
        return

    df = st.session_state.df
    st.markdown('<div class="section"><h3>2 · Analyze</h3></div>', unsafe_allow_html=True)
    left, right = st.columns([4, 1.5])
    with left:
        st.markdown(
            f'<div class="card"><b>{st.session_state.source_name}</b><br>'
            f'<span class="muted">{len(df):,} invoice rows · {len(df.columns)} columns · schema validated by the analysis engine</span></div>',
            unsafe_allow_html=True,
        )
    with right:
        if st.button("✦ ANALYZE INVOICES", key="analyze_btn", type="primary", width="stretch"):
            run_analysis()
            st.rerun()

    st.markdown("### Source preview")
    st.dataframe(df.head(100), width="stretch", hide_index=True)

    if not st.session_state.analyzed:
        st.markdown(
            '<div class="card"><h3>Ready to analyze</h3>'
            '<p class="muted">Run the analysis to see policy decisions, ML risk, neural anomaly scores, evidence and the human-review queue.</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="footer">FINSIGHT · READY FOR ANALYSIS</div>', unsafe_allow_html=True)
        return

    st.markdown('<div class="section"><h3>3 · Results</h3></div>', unsafe_allow_html=True)
    render_results()

    tabs = st.tabs(["Review queue", "Evidence", "Copilot", "Audit & system"])
    with tabs[0]:
        review_tab()
    with tabs[1]:
        evidence_tab()
    with tabs[2]:
        copilot_tab()
    with tabs[3]:
        system_tab()

    st.markdown('<div class="footer">FINSIGHT · DETERMINISTIC RULES ARE THE SOURCE OF TRUTH · AI IS ADVISORY · HUMAN JUDGMENT</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
