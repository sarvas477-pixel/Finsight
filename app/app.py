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

/* FinSight dashboard shell */
[data-testid="stSidebar"]{background:#08111f!important;border-right:1px solid #1d3047!important}
[data-testid="stSidebar"]>div{padding-top:18px!important}
.side-brand{font:700 20px "Space Grotesk";letter-spacing:-.04em;padding:4px 8px 20px;border-bottom:1px solid #1d3047;margin-bottom:14px}
.side-brand b{color:#19d9ff}
.side-section{font:700 9px "Space Grotesk";letter-spacing:.14em;color:#61758e!important;margin:18px 8px 7px;text-transform:uppercase}
.side-copy{color:#71859d!important;font-size:11px;line-height:1.5;padding:0 8px 12px}
.topline{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1d3047;padding-bottom:16px;margin-bottom:22px}
.crumb{font:600 11px "Space Grotesk";color:#6f839c!important;letter-spacing:.03em}
.userpill{font:600 11px "Space Grotesk";color:#b8c7d9!important;background:#0c1a2c;border:1px solid #20354e;border-radius:999px;padding:8px 12px}
.dash-grid{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(280px,.8fr);gap:16px}
.card{background:#0b1727;border:1px solid #20344d;border-radius:16px;padding:18px}
.card-title{font:700 11px "Space Grotesk";letter-spacing:.1em;color:#9eb0c4!important;text-transform:uppercase}
.card-value{font:700 30px "Space Grotesk";margin-top:8px;color:#f4f8ff}
.rowitem{display:flex;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid #172940}
.rowitem:last-child{border-bottom:0}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:8px}
.dot-cyan{background:#19d9ff}.dot-green{background:#36d48a}.dot-red{background:#ff6175}.dot-amber{background:#f5b942}
@media(max-width:900px){.dash-grid{grid-template-columns:1fr}}
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



def set_page(page):
    st.session_state.page = page


def page_nav():
    st.session_state.setdefault("page", "Dashboard")
    with st.sidebar:
        st.markdown('<div class="side-brand">Fin<b>◈</b>Sight</div>', unsafe_allow_html=True)
        st.markdown('<div class="side-copy">Accounts-payable intelligence<br><span style="color:#36d48a">● ENGINE ONLINE</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="side-section">Workspace</div>', unsafe_allow_html=True)
        items = [
            ("Dashboard", "⌂ Dashboard"),
            ("Exceptions", "⚠ Exceptions"),
            ("Evidence", "◉ Evidence"),
            ("Copilot", "✦ Copilot"),
            ("Audit", "▤ Audit log"),
        ]
        for page, label in items:
            if st.button(label, key="nav_" + page.lower(), width="stretch"):
                set_page(page)
                st.rerun()
        st.markdown('<div class="side-section">System</div>', unsafe_allow_html=True)
        if st.button("↻ New batch", key="nav_new", width="stretch"):
            reset_workspace()
            set_page("Dashboard")
            st.rerun()
        if st.button("↪ Log out", key="nav_logout", width="stretch"):
            st.session_state["authenticated"] = False
            st.rerun()
        st.markdown('<div class="side-copy" style="margin-top:20px">Required CSV fields<br>invoice_id · vendor · amount<br>category · invoice_date</div>', unsafe_allow_html=True)


def topbar():
    st.markdown(
        '<div class="topline"><div class="crumb">FinSight / AP Intelligence / '
        + st.session_state.get("page", "Dashboard")
        + '</div><div class="userpill">● SYSTEM READY &nbsp; · &nbsp; AP CONTROL</div></div>',
        unsafe_allow_html=True,
    )


def dashboard_page():
    if st.session_state.df is None:
        st.markdown(
            '<div class="hero"><div class="kicker">ACCOUNTS PAYABLE · CONTROL CENTER</div>'
            '<h1>Make every invoice<br><span>easy to trust.</span></h1>'
            '<p>Upload a batch, run deterministic checks, then resolve exceptions with evidence and human review in one workspace.</p></div>',
            unsafe_allow_html=True,
        )
        left, right = st.columns([1.5, .8])
        with left:
            st.markdown('<div class="card"><div class="card-title">Invoice intake</div><h3>Load a new batch</h3><p class="muted">CSV only · required fields: invoice_id, vendor, amount, category, invoice_date</p>', unsafe_allow_html=True)
            uploaded = st.file_uploader("Drop invoice CSV here", type=["csv"], key="invoice_upload")
            st.markdown('</div>', unsafe_allow_html=True)
            if uploaded is not None and uploaded.name != st.session_state.source_name:
                try:
                    reset_workspace(pd.read_csv(uploaded), uploaded.name)
                    st.session_state.page = "Dashboard"
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not read CSV: {exc}")
        with right:
            st.markdown('<div class="card"><div class="card-title">Quick start</div><h3>Demo batch</h3><p class="muted">Use the bundled dataset to test the complete FinSight workflow.</p>', unsafe_allow_html=True)
            if st.button("Load sample batch", key="load_sample", type="primary", width="stretch"):
                reset_workspace(load_sample(), "data/invoices.csv")
                st.session_state.page = "Dashboard"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("### Workflow")
        a,b,c=st.columns(3)
        for col,title,body,dot in [
            (a,"Analyze","Deterministic rules inspect every invoice.","cyan"),
            (b,"Resolve","Exceptions are routed to human review.","red"),
            (c,"Explain","Evidence makes each decision traceable.","green"),
        ]:
            with col:
                st.markdown(f'<div class="card"><span class="dot dot-{dot}"></span><b>{title}</b><p class="muted">{body}</p></div>',unsafe_allow_html=True)
        return

    if not st.session_state.analyzed:
        st.markdown(
            f'<div class="hero"><div class="kicker">BATCH READY</div><h1>{st.session_state.source_name}<br><span>{len(st.session_state.df):,} invoices loaded.</span></h1>'
            '<p>Preview the source and run the deterministic engine when you are ready.</p></div>',
            unsafe_allow_html=True,
        )
        a,b,c=st.columns([4,1.1,1])
        with a:
            st.markdown(f'<div class="card"><div class="card-title">Current batch</div><div class="card-value">{len(st.session_state.df):,}</div><span class="muted">invoice rows · {len(st.session_state.df.columns)} columns</span></div>',unsafe_allow_html=True)
        with b:
            if st.button("Analyze",key="analyze_btn",type="primary",width="stretch"):
                run_analysis(); st.rerun()
        with c:
            if st.button("Reset",key="reset_workspace",width="stretch"):
                reset_workspace(); st.rerun()
        with st.expander("Preview source CSV"):
            st.dataframe(st.session_state.df.head(100),width="stretch",hide_index=True)
        return

    results=st.session_state.results
    summary=summarize_results(results)
    avg=sum(float(r.get("confidence",0)) for r in results)/len(results) if results else 0
    st.markdown(
        '<div class="hero"><div class="kicker">CONTROL CENTER · ANALYSIS COMPLETE</div>'
        '<h1>Make sense of<br><span>every decision.</span></h1>'
        '<p>Latest batch: '+str(st.session_state.source_name)+' · '+str(summary["total"])+' invoices analyzed.</p></div>',
        unsafe_allow_html=True,
    )
    metrics(results)
    st.markdown('<div class="dash-grid">',unsafe_allow_html=True)
    st.markdown(
        '<div class="card"><div class="card-title">Recent decisions</div>',
        unsafe_allow_html=True,
    )
    out=build_results_df(results)
    for _,row in out.head(5).iterrows():
        status=str(row["status"])
        dot="green" if status=="CLEAN" else "red"
        st.markdown(
            f'<div class="rowitem"><div><span class="dot dot-{dot}"></span><b>{row["invoice_id"]}</b><br><span class="muted">{row["vendor"]} · {row["category"]}</span></div>'
            f'<div><b>{status}</b><br><span class="muted">{float(row["confidence"]):.0%} confidence</span></div></div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>',unsafe_allow_html=True)
    st.markdown(
        f'<div><div class="card"><div class="card-title">Today’s AP note</div><h3>{summary["exceptions"]} exceptions</h3>'
        f'<p class="muted">{summary["review_required"]} invoices are routed to human review. Review decisions remain separate from the rule engine.</p></div>'
        f'<div style="height:16px"></div><div class="card"><div class="card-title">My files</div><h3>{st.session_state.source_name}</h3>'
        f'<p class="muted">{len(st.session_state.df):,} rows · analyzed just now</p></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>',unsafe_allow_html=True)
    st.markdown("### Analysis workspace")
    tabs=st.tabs(["Decisions","Review","Evidence","Copilot"])
    with tabs[0]: render_results()
    with tabs[1]: review_tab()
    with tabs[2]: evidence_tab()
    with tabs[3]: copilot_tab()


def exceptions_page():
    st.markdown('<div class="hero"><div class="kicker">HUMAN REVIEW</div><h1>Resolve the<br><span>exception queue.</span></h1><p>Every flagged invoice is shown with its reason and evidence before a human decision.</p></div>',unsafe_allow_html=True)
    if not st.session_state.analyzed:
        st.info("Analyze an invoice batch first.")
        return
    review_tab()


def evidence_page():
    st.markdown('<div class="hero"><div class="kicker">TRACEABILITY</div><h1>See the<br><span>evidence.</span></h1><p>Inspect the exact rule IDs, trusted record fields and matched invoice evidence behind each decision.</p></div>',unsafe_allow_html=True)
    if not st.session_state.analyzed:
        st.info("Analyze an invoice batch first.")
        return
    evidence_tab()


def copilot_page():
    st.markdown('<div class="hero"><div class="kicker">FIN·LLM COPILOT</div><h1>Ask about<br><span>your AP data.</span></h1><p>Copilot answers FinSight-scoped questions and cites the available workflow context.</p></div>',unsafe_allow_html=True)
    if not st.session_state.analyzed:
        st.info("Analyze a batch first for invoice-specific answers.")
    copilot_tab()


def audit_page():
    st.markdown('<div class="hero"><div class="kicker">AUDIT TRAIL</div><h1>Every action<br><span>has a record.</span></h1><p>Analysis and human-review actions are captured for traceability.</p></div>',unsafe_allow_html=True)
    if st.session_state.audit:
        st.dataframe(pd.DataFrame(st.session_state.audit),width="stretch",hide_index=True)
    else:
        st.info("No audit events yet.")
    with st.expander("Engine configuration"):
        st.write({"required_columns": REQUIRED_COLUMNS, "category_limits": CATEGORY_LIMITS})


def main():
    page_nav()
    topbar()
    page = st.session_state.get("page", "Dashboard")
    if page == "Dashboard":
        dashboard_page()
    elif page == "Exceptions":
        exceptions_page()
    elif page == "Evidence":
        evidence_page()
    elif page == "Copilot":
        copilot_page()
    elif page == "Audit":
        audit_page()
    st.markdown('<div class="footer">FINSIGHT · DETERMINISTIC ENGINE IS THE SOURCE OF TRUTH · AI EXPLAINS, NEVER DECIDES</div>', unsafe_allow_html=True)


init_state()
if require_login():
    main()
