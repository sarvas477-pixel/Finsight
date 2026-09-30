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

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#06101d;--surface:#0b1727;--surface2:#0f1e31;--line:#20344d;--text:#f4f8ff;--muted:#8fa3bb;--cyan:#19d9ff;--blue:#4c8dff;--green:#36d48a;--amber:#f5b942;--red:#ff6175}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:var(--bg)!important;color:var(--text)!important}
body,[class*="css"]{font-family:Inter,sans-serif}
[data-testid="stHeader"]{background:rgba(6,16,29,.9)!important}
.block-container{max-width:1440px;padding:22px 34px 60px}
h1,h2,h3,h4{font-family:"Space Grotesk",sans-serif!important;color:var(--text)!important}
p,span,label{color:var(--text)}
.nav{display:flex;align-items:center;justify-content:space-between;padding:8px 0 22px;border-bottom:1px solid var(--line);margin-bottom:28px}
.logo{font:700 1.35rem "Space Grotesk";letter-spacing:-.04em}.logo span{color:var(--cyan)}
.status{border:1px solid rgba(54,212,138,.25);background:rgba(54,212,138,.08);color:var(--green)!important;border-radius:999px;padding:7px 12px;font:700 .65rem "Space Grotesk";letter-spacing:.08em}
.hero{padding:4px 0 28px}.kicker{color:var(--cyan)!important;font:700 .68rem "Space Grotesk";letter-spacing:.15em}
.hero h1{font-size:clamp(2.6rem,5vw,4.8rem);line-height:.96;letter-spacing:-.065em;margin:12px 0}
.hero h1 span{color:var(--cyan)}.hero p{max-width:720px;color:var(--muted)!important;line-height:1.65}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:22px;box-shadow:0 16px 40px rgba(0,0,0,.2)}
.panel-title{font:700 .7rem "Space Grotesk";letter-spacing:.12em;color:var(--muted)!important;text-transform:uppercase;margin-bottom:10px}
.dropzone [data-testid="stFileUploader"] section{background:var(--surface2)!important;border:1px dashed #31506f!important;border-radius:14px!important}
.metric{background:var(--surface);border:1px solid var(--line);border-radius:13px;padding:17px}.metric small{display:block;color:var(--muted)!important;font:700 .63rem "Space Grotesk";letter-spacing:.1em;text-transform:uppercase}.metric strong{display:block;font:700 1.9rem "Space Grotesk";margin-top:6px}
.safe strong{color:var(--green)}.flag strong{color:var(--red)}.review strong{color:var(--amber)}.score strong{color:var(--cyan)}
div.stButton>button,div.stDownloadButton>button{min-height:42px!important;border-radius:9px!important;border:1px solid #29435e!important;background:var(--surface2)!important;color:var(--text)!important;font:600 13px "Space Grotesk"!important}
div.stButton>button:hover,div.stDownloadButton>button:hover{border-color:var(--cyan)!important;transform:translateY(-1px)}
button[kind="primary"]{background:linear-gradient(135deg,#19d9ff,#4c8dff)!important;color:#03111e!important;border:0!important}
.stTextInput>div>div,.stTextArea>div>div,[data-baseweb="select"]>div{background:#081321!important;border-color:#29435e!important;color:var(--text)!important}
[data-testid="stFileUploader"] section{background:var(--surface2)!important;border-color:#31506f!important}
[data-testid="stDataFrame"]{border:1px solid var(--line)!important;border-radius:12px!important;overflow:hidden}
[data-testid="stTabs"] [role="tab"]{color:var(--muted)!important;font:700 12px "Space Grotesk"!important}
[data-testid="stTabs"] [aria-selected="true"]{color:var(--cyan)!important}
[data-testid="stChatMessage"],[data-testid="stExpander"]{background:var(--surface)!important;border:1px solid var(--line)!important}
.badge{display:inline-block;border-radius:999px;padding:5px 9px;border:1px solid var(--line);font:700 .65rem "Space Grotesk"}
.clean{color:var(--green)!important}.exception{color:var(--red)!important}.human{color:var(--amber)!important}
.muted{color:var(--muted)!important}.footer{margin-top:40px;text-align:center;color:#53677f!important;font:700 .6rem "Space Grotesk";letter-spacing:.14em}
hr{border-color:var(--line)!important}
</style>""", unsafe_allow_html=True)


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
    st.markdown(
        '<div class="nav"><div class="logo">Fin<span>Sight</span> <small>/ AP INTELLIGENCE</small></div>'
        '<div class="status">● RULE ENGINE ONLINE</div></div>',
        unsafe_allow_html=True,
    )

    if st.session_state.df is None:
        st.markdown(
            '<div class="hero"><div class="kicker">INVOICE INTELLIGENCE</div>'
            '<h1>Know every invoice.<br><span>Trust every decision.</span></h1>'
            '<p>A focused workspace for invoice analysis, exceptions, evidence and human review. '
            'The deterministic rule engine stays the source of truth.</p></div>',
            unsafe_allow_html=True,
        )

        left, right = st.columns([1.55, 1])
        with left:
            st.markdown('<div class="panel-title">01 · Load data</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="panel"><h3>Upload your invoice CSV</h3>'
                '<p class="muted">Required columns: invoice_id, vendor, amount, category, invoice_date.</p></div>',
                unsafe_allow_html=True,
            )
            uploaded = st.file_uploader("Invoice CSV", type=["csv"], key="invoice_upload")
        with right:
            st.markdown('<div class="panel-title">Quick start</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="panel"><h3>Test with sample data</h3>'
                '<p class="muted">Load the bundled five-invoice dataset and run the complete workflow.</p></div>',
                unsafe_allow_html=True,
            )
            if st.button("Load sample dataset", key="load_sample", type="primary", width="stretch"):
                reset_workspace(load_sample(), "data/invoices.csv")
                st.rerun()

        if uploaded is not None and uploaded.name != st.session_state.source_name:
            try:
                reset_workspace(pd.read_csv(uploaded), uploaded.name)
                st.rerun()
            except Exception as exc:
                st.error(f"Could not read CSV: {exc}")

        st.markdown("### The workflow")
        a, b, c = st.columns(3)
        for col, title, body in [
            (a, "01 · Analyze", "Deterministic rules produce each invoice decision."),
            (b, "02 · Review", "Exceptions and uncertain cases go to a human."),
            (c, "03 · Explain", "Evidence and rule IDs show exactly why a result happened."),
        ]:
            with col:
                st.markdown(
                    f'<div class="panel"><h4>{title}</h4><p class="muted">{body}</p></div>',
                    unsafe_allow_html=True,
                )
        st.markdown('<div class="footer">FINSIGHT · RULES FIRST · HUMAN JUDGMENT</div>', unsafe_allow_html=True)
        return

    st.markdown(
        f'<div class="hero"><div class="kicker">WORKSPACE · {st.session_state.source_name.upper()}</div>'
        f'<h1>Ready to <span>analyze.</span></h1>'
        f'<p>{len(st.session_state.df):,} invoice rows loaded. Run the deterministic engine, then review every decision from one screen.</p></div>',
        unsafe_allow_html=True,
    )

    a, b, c = st.columns([4, 1.2, 1])
    with a:
        st.markdown(
            f'<div class="panel"><b>{st.session_state.source_name}</b><br>'
            f'<span class="muted">{len(st.session_state.df):,} rows · {len(st.session_state.df.columns)} columns</span></div>',
            unsafe_allow_html=True,
        )
    with b:
        if st.button("Analyze", key="analyze_btn", type="primary", width="stretch"):
            run_analysis()
            st.rerun()
    with c:
        if st.button("Reset", key="reset_workspace", width="stretch"):
            reset_workspace()
            st.rerun()

    with st.expander("Preview uploaded data"):
        st.dataframe(st.session_state.df.head(100), width="stretch", hide_index=True)

    if not st.session_state.analyzed:
        st.info("Ready. Click Analyze to generate invoice decisions.")
        st.markdown('<div class="footer">FINSIGHT · READY</div>', unsafe_allow_html=True)
        return

    st.markdown("### Results")
    tabs = st.tabs(["Decisions", "Review", "Evidence", "Copilot"])
    with tabs[0]:
        render_results()
    with tabs[1]:
        review_tab()
    with tabs[2]:
        evidence_tab()
    with tabs[3]:
        copilot_tab()

    with st.expander("Session audit & system status"):
        if st.session_state.audit:
            st.dataframe(pd.DataFrame(st.session_state.audit), width="stretch", hide_index=True)
        else:
            st.info("No audit events yet.")
        st.caption("Required schema")
        st.code(", ".join(REQUIRED_COLUMNS))
        st.caption("Configured category limits")
        st.write(CATEGORY_LIMITS)

    st.markdown(
        '<div class="footer">FINSIGHT · DETERMINISTIC ENGINE IS THE SOURCE OF TRUTH · AI EXPLAINS, NEVER DECIDES</div>',
        unsafe_allow_html=True,
    )


init_state()
if require_login():
    main()
