"""FinSight — premium Streamlit accounts-payable intelligence workspace."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import CATEGORY_LIMITS, REQUIRED_COLUMNS
from src.rule_engine import process_invoices, summarize_results


st.set_page_config(
    page_title="FinSight · AP Intelligence",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{
 --bg:#f5f7fb;--surface:#ffffff;--surface2:#f8f9fd;--line:#e7e9f0;
 --text:#151827;--muted:#687085;--violet:#6d4aff;--pink:#e84a91;
 --cyan:#08a8c7;--green:#119b68;--amber:#b87900;--red:#d9365f;
}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:linear-gradient(180deg,#fbfcff 0%,#f3f5fa 100%)!important;color:var(--text)!important}
body,[class*="css"]{font-family:'DM Sans',sans-serif}
[data-testid="stHeader"]{background:rgba(255,255,255,.82)!important;border-bottom:1px solid var(--line)}
.block-container{max-width:1540px;padding:28px 38px 70px}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;color:var(--text)!important}
p,label,span,.stMarkdown{color:var(--text)}
[data-testid="stSidebar"],[data-testid="stSidebar"]>div{background:#fff!important;border-right:1px solid var(--line)!important}
[data-testid="stSidebar"] *{color:var(--text)!important}
[data-testid="stSidebar"] .stCaption{color:var(--muted)!important}
hr{border-color:var(--line)!important}
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}
.brand{font:700 1.2rem 'Space Grotesk';letter-spacing:-.04em}.brand span{color:var(--violet)}
.status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 10px rgba(17,155,104,.35);margin-right:7px}
.hero{position:relative;overflow:hidden;border:1px solid #e4e5ef;border-radius:30px;padding:44px;background:
 radial-gradient(circle at 78% 18%,rgba(109,74,255,.16),transparent 27%),
 radial-gradient(circle at 92% 82%,rgba(8,168,199,.11),transparent 25%),
 linear-gradient(135deg,#fff,#f4f1ff 72%,#eefcff);box-shadow:0 25px 70px rgba(41,45,75,.10)}
.hero:before{content:"";position:absolute;inset:-2px;background:linear-gradient(110deg,transparent 20%,rgba(255,255,255,.75) 45%,transparent 65%);transform:translateX(-100%);animation:scan 7s ease-in-out infinite}
.hero-grid{display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:30px;align-items:center;position:relative}
.eyebrow{font-size:.68rem;font-weight:800;letter-spacing:.22em;color:#6846db!important}
.hero h1{font-size:clamp(3rem,6vw,6.4rem);line-height:.88;letter-spacing:-.075em;margin:16px 0 22px}
.hero h1 span{background:linear-gradient(90deg,#e03c88,#6948e9,#079ab7);-webkit-background-clip:text;color:transparent}
.hero p{max-width:720px;color:#596278!important;font-size:1.05rem;line-height:1.7}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:24px}.chip{border:1px solid #dddff0;background:rgba(255,255,255,.75);border-radius:999px;padding:8px 12px;font-size:.73rem;color:#4e566c!important}
.orb{height:290px;position:relative;display:grid;place-items:center}.orb-core{width:100px;height:100px;border-radius:30px;display:grid;place-items:center;background:linear-gradient(135deg,#ed5a9d,#6d4aff);font-size:2rem;color:#fff!important;box-shadow:0 18px 45px rgba(109,74,255,.25);animation:float 4s ease-in-out infinite;z-index:2}.ring{position:absolute;border:1px solid rgba(109,74,255,.2);border-radius:50%;animation:spin 15s linear infinite}.r1{width:180px;height:180px}.r2{width:285px;height:285px;border-color:rgba(8,168,199,.16);animation-duration:22s;animation-direction:reverse}
.section{font:700 1.55rem 'Space Grotesk';letter-spacing:-.04em;margin:34px 0 14px}
.panel,.metric,.feature,.copilot{background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:22px;box-shadow:0 15px 45px rgba(41,45,75,.07)}
.panel{padding:22px}.feature{padding:22px;min-height:145px;transition:.22s}.feature:hover{transform:translateY(-3px);border-color:#d3c9ff;box-shadow:0 20px 50px rgba(41,45,75,.11)}
.feature .icon{font-size:1.5rem;color:var(--violet)!important}.feature h3{margin:10px 0 5px}.feature p,.muted{color:var(--muted)!important;line-height:1.55}
.metric{padding:18px;min-height:100px}.metric small{display:block;color:var(--muted)!important;font-size:.66rem;text-transform:uppercase;letter-spacing:.15em}.metric strong{display:block;font:700 2.05rem 'Space Grotesk';margin-top:8px}.metric.safe strong{color:var(--green)}.metric.flagged strong{color:var(--red)}.metric.attention strong{color:var(--amber)}.metric.score strong{color:var(--cyan)}
.badge{display:inline-flex;align-items:center;gap:7px;border:1px solid #e1e3ec;border-radius:999px;padding:6px 10px;font-size:.7rem;font-weight:700;background:#fff}
.badge.clean{color:var(--green)!important}.badge.exception{color:var(--red)!important}.badge.review{color:var(--amber)!important}
.copilot{padding:28px;background:radial-gradient(circle at 90% 0,rgba(109,74,255,.13),transparent 38%),#fff}
.copilot h2{font-size:2.6rem;margin:7px 0}.copilot p{color:var(--muted)!important}
div.stButton>button,div.stDownloadButton>button{border-radius:13px!important;border:1px solid #dfe2ea!important;background:#fff!important;color:#22283a!important;min-height:44px!important;font-weight:700!important;transition:.2s!important;box-shadow:0 4px 12px rgba(41,45,75,.04)}
div.stButton>button:hover,div.stDownloadButton>button:hover{border-color:#bfb1ff!important;transform:translateY(-1px)!important;box-shadow:0 10px 25px rgba(41,45,75,.10)!important}
button[kind="primary"]{background:linear-gradient(100deg,#e84a91,#6d4aff)!important;border:0!important;color:white!important;box-shadow:0 12px 30px rgba(109,74,255,.20)!important}
[data-testid="stFileUploader"],[data-testid="stFileUploader"] section,[data-testid="stFileUploader"] section>div{background:#fff!important;border:1px dashed #cdd1df!important;border-radius:18px!important}
[data-testid="stFileUploader"] button{background:#f7f8fc!important;color:#252a3b!important;border:1px solid #dfe2ea!important}
.stTextInput>div>div,.stTextArea>div>div,.stSelectbox>div>div,.stNumberInput>div>div,input,textarea,[data-baseweb="select"]>div{background:#fff!important;color:#1a1f30!important;border-color:#d9dce6!important}
input::placeholder,textarea::placeholder{color:#8b92a4!important}
[data-baseweb="popover"],[data-baseweb="menu"]{background:#fff!important;color:#1a1f30!important;border:1px solid #dfe2ea!important}[data-baseweb="menu"] *{color:#1a1f30!important}
[data-testid="stDataFrame"],[data-testid="stDataFrame"]>div{background:#fff!important;border:1px solid var(--line)!important;border-radius:16px!important;overflow:hidden}
[data-testid="stTabs"] [role="tab"]{color:#687085!important}.stTabs [aria-selected="true"]{color:#6846db!important}
[data-testid="stChatMessage"]{background:#fff!important;border:1px solid var(--line)!important;border-radius:18px!important;margin-bottom:9px}
[data-testid="stChatInput"]{background:#fff!important;border-color:#d9dce6!important}[data-testid="stChatInput"] textarea{background:#fff!important;color:#1a1f30!important}
[data-testid="stExpander"]{background:#fff!important;border:1px solid var(--line)!important;border-radius:16px!important}
.stAlert{background:#fff!important;color:#1a1f30!important;border:1px solid var(--line)!important}
.footer{text-align:center;color:#8990a2!important;font-size:.65rem;letter-spacing:.15em;margin-top:48px}
@keyframes scan{0%,55%{transform:translateX(-100%)}80%,100%{transform:translateX(100%)}}@keyframes float{50%{transform:translateY(-11px) rotate(3deg)}}@keyframes spin{to{transform:rotate(360deg)}}
@media(max-width:900px){.block-container{padding:18px 14px 50px}.hero{padding:28px}.hero-grid{grid-template-columns:1fr}.orb{height:180px}.hero h1{font-size:3.7rem}}
</style>
""",
    unsafe_allow_html=True,
)


def init_state() -> None:
    defaults = {
        "df": None, "source_name": "", "results": [], "analyzed": False,
        "audit": [], "reviews": {}, "chat": [], "page": "Overview",
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def reset_workspace(df: pd.DataFrame | None = None, source_name: str = "") -> None:
    st.session_state.df = df
    st.session_state.source_name = source_name
    st.session_state.results = []
    st.session_state.analyzed = False
    st.session_state.audit = []
    st.session_state.reviews = {}
    st.session_state.chat = []


def load_sample() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "invoices.csv")


def add_audit(event: str, invoice_id: str = "", message: str = "", metadata: dict | None = None) -> None:
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


def analyze(df: pd.DataFrame) -> list[dict]:
    return process_invoices(df)


def build_results_df(results: list[dict]) -> pd.DataFrame:
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


def explain(r: dict) -> str:
    if r.get("status") == "CLEAN":
        return f"{r.get('invoice_id')} passed every configured deterministic check and is AUTO-PASS."
    reasons = " ".join(str(x.get("message", "")) for x in r.get("reasons", []))
    return f"{r.get('invoice_id')} is an EXCEPTION and is routed to {r.get('route')}. {reasons}"


def run_analysis() -> None:
    df = st.session_state.df
    if df is None:
        st.warning("Upload a CSV or load the sample first.")
        return
    try:
        results = analyze(df)
        st.session_state.results = results
        st.session_state.analyzed = True
        s = summarize_results(results)
        add_audit("ANALYSIS_RUN", "", f"{st.session_state.source_name}: {s['total']} invoices analyzed.", {"summary": s})
        for r in results:
            add_audit("DECISION", r.get("invoice_id", ""), f"{r.get('status')} / {r.get('route')}", {"rule_ids": r.get("rule_ids", []), "confidence": r.get("confidence")})
        st.toast("Analysis complete", icon="✨")
    except Exception as exc:
        st.session_state.analyzed = False
        st.error(f"Analysis failed: {exc}")


def sidebar() -> None:
    with st.sidebar:
        st.markdown("## ✦ FinSight")
        st.caption("AP intelligence workspace")
        st.markdown('<span class="badge"><span class="status-dot"></span>Deterministic engine online</span>', unsafe_allow_html=True)
        st.divider()
        pages = ["Overview", "Analyze", "Review", "Evidence", "Copilot", "System"]
        page = st.radio(
            "Workspace",
            pages,
            index=pages.index(st.session_state.page),
            key="nav_page",
            label_visibility="collapsed",
        )
        if page != st.session_state.page:
            st.session_state.page = page
            st.rerun()
        st.divider()
        uploaded = st.file_uploader("Invoice CSV", type=["csv"], help="Required: invoice_id, vendor, amount, category, invoice_date")
        if uploaded is not None and uploaded.name != st.session_state.source_name:
            try:
                reset_workspace(pd.read_csv(uploaded), uploaded.name)
                st.toast(f"{uploaded.name} loaded", icon="✨")
            except Exception as exc:
                st.error(f"Could not read CSV: {exc}")
        a, b = st.columns(2)
        with a:
            if st.button("Load sample", width="stretch"):
                reset_workspace(load_sample(), "data/invoices.csv")
                st.rerun()
        with b:
            if st.button("Reset", width="stretch"):
                reset_workspace()
                st.rerun()
        st.divider()
        st.caption("Required columns")
        st.code("\n".join(REQUIRED_COLUMNS), language="text")
        st.caption("Configured limits")
        for cat, limit in CATEGORY_LIMITS.items():
            st.write(f"{cat} · ₹{limit:,.0f}")


def topbar() -> None:
    source = st.session_state.source_name or "No dataset loaded"
    st.markdown(
        f'<div class="topbar"><div class="brand">FINSIGHT <span>/ AP INTELLIGENCE</span></div>'
        f'<div class="badge"><span class="status-dot"></span>{source}</div></div>',
        unsafe_allow_html=True,
    )


def hero() -> None:
    st.markdown(
        """
<div class="hero"><div class="hero-grid"><div>
<div class="eyebrow">FINANCE OPERATIONS · RULES + EVIDENCE + AI</div>
<h1>Turn the<br><span>exception pile</span><br>into clarity.</h1>
<p>Analyze invoice CSVs with deterministic rules, see the exact evidence behind every decision, route uncertain cases to humans, and ask FinSight Copilot to explain the result.</p>
<div class="chips"><span class="chip">Deterministic decisions</span><span class="chip">Human review</span><span class="chip">Audit trail</span><span class="chip">AI explanations</span></div>
</div><div class="orb"><div class="orb-core">✦</div><div class="ring r1"></div><div class="ring r2"></div></div></div></div>
""",
        unsafe_allow_html=True,
    )


def metrics(results: list[dict]) -> None:
    s = summarize_results(results)
    avg = sum(float(r.get("confidence", 0)) for r in results) / len(results) if results else 0
    vals = [("Invoices", s["total"], ""), ("Auto-pass", s["clean"], "safe"), ("Exceptions", s["exceptions"], "flagged"), ("Human review", s["review_required"], "attention"), ("Confidence", f"{avg:.0%}", "score")]
    cols = st.columns(5)
    for c, (label, value, kind) in zip(cols, vals):
        with c:
            st.markdown(f'<div class="metric {kind}"><small>{label}</small><strong>{value}</strong></div>', unsafe_allow_html=True)


def analysis_page() -> None:
    st.markdown('<div class="section">Analyze</div>', unsafe_allow_html=True)
    if st.session_state.df is None:
        st.markdown('<div class="panel"><h3>Start with an invoice CSV</h3><p class="muted">Use the uploader in the sidebar or load the bundled sample. FinSight will validate the schema before running the rule engine.</p></div>', unsafe_allow_html=True)
        return
    df = st.session_state.df
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown(f"**{st.session_state.source_name}** · {len(df):,} source rows")
        st.caption("Required schema: " + " · ".join(REQUIRED_COLUMNS))
    with c2:
        if st.button("✦ Analyze now", type="primary", width="stretch"):
            run_analysis()
    st.markdown('<div class="section">Source preview</div>', unsafe_allow_html=True)
    st.dataframe(df.head(100), width="stretch", hide_index=True)
    if not st.session_state.analyzed:
        return
    results = st.session_state.results
    st.markdown('<div class="section">Decision stream</div>', unsafe_allow_html=True)
    metrics(results)
    out = build_results_df(results)
    st.dataframe(
        out[["invoice_id","vendor","amount","category","status","route","confidence","human_review_required"]],
        width="stretch", hide_index=True,
        column_config={"confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1, format="%.0f%%")},
    )
    exceptions = out[out.status == "EXCEPTION"].copy()
    if not exceptions.empty:
        st.markdown('<div class="section">Exception details</div>', unsafe_allow_html=True)
        st.dataframe(exceptions[["invoice_id","vendor","amount","category","rule_ids","reasons","route"]], width="stretch", hide_index=True)
    x, y, z = st.columns(3)
    with x:
        st.download_button("↓ Analyzed CSV", out.to_csv(index=False).encode(), "finsight_analyzed.csv", "text/csv", width="stretch")
    with y:
        st.download_button(f"↓ Exceptions ({len(exceptions)})", exceptions.to_csv(index=False).encode(), "finsight_exceptions.csv", "text/csv", width="stretch")
    with z:
        st.download_button("↓ Original CSV", df.to_csv(index=False).encode(), "finsight_original.csv", "text/csv", width="stretch")


def review_page() -> None:
    st.markdown('<div class="section">Human review queue</div>', unsafe_allow_html=True)
    items = [r for r in st.session_state.results if r.get("human_review_required")]
    if not items:
        st.info("No invoices currently require human review.")
        return
    st.caption(f"{len(items)} invoice(s) require a human decision. FinSight does not let AI approve or reject them.")
    for r in items:
        iid = str(r.get("invoice_id"))
        old = st.session_state.reviews.get(iid, {})
        with st.container(border=True):
            st.markdown(f"### {iid}")
            st.write(explain(r))
            with st.expander("Evidence & reasons", expanded=False):
                st.json({"evidence": r.get("evidence"), "rule_ids": r.get("rule_ids"), "reasons": r.get("reasons"), "confidence": r.get("confidence")})
            note = st.text_area("Reviewer note", value=old.get("comment", ""), key=f"review_note_{iid}")
            a, b = st.columns(2)
            with a:
                if st.button("Approve", key=f"approve_{iid}", width="stretch"):
                    st.session_state.reviews[iid] = {"action":"APPROVED","comment":note.strip(),"timestamp":pd.Timestamp.now(tz="UTC").isoformat()}
                    add_audit("REVIEW_ACTION", iid, f"APPROVED: {note.strip()}")
                    try:
                        from src.persistence import save_review_action
                        save_review_action(iid, "APPROVED", note.strip())
                    except Exception:
                        pass
                    st.success(f"{iid} marked APPROVED.")
            with b:
                if st.button("Reject", key=f"reject_{iid}", width="stretch"):
                    st.session_state.reviews[iid] = {"action":"REJECTED","comment":note.strip(),"timestamp":pd.Timestamp.now(tz="UTC").isoformat()}
                    add_audit("REVIEW_ACTION", iid, f"REJECTED: {note.strip()}")
                    try:
                        from src.persistence import save_review_action
                        save_review_action(iid, "REJECTED", note.strip())
                    except Exception:
                        pass
                    st.warning(f"{iid} marked REJECTED.")


def evidence_page() -> None:
    st.markdown('<div class="section">Evidence explorer</div>', unsafe_allow_html=True)
    if not st.session_state.results:
        st.info("Analyze a CSV first.")
        return
    ids = [str(r.get("invoice_id")) for r in st.session_state.results]
    selected = st.selectbox("Invoice", ids)
    r = next(x for x in st.session_state.results if str(x.get("invoice_id")) == selected)
    badge = "clean" if r.get("status") == "CLEAN" else "exception"
    st.markdown(f'<span class="badge {badge}">● {r.get("status")}</span> <span class="badge">{r.get("route")}</span>', unsafe_allow_html=True)
    a,b,c = st.columns(3)
    a.metric("Confidence", f"{float(r.get('confidence',0)):.0%}")
    b.metric("Rule flags", len(r.get("rule_ids") or []))
    c.metric("Human review", "Required" if r.get("human_review_required") else "Not required")
    st.markdown('<div class="section">Why this happened</div>', unsafe_allow_html=True)
    if not r.get("reasons"):
        st.success("No rule violations. This invoice passed all configured checks.")
    else:
        for reason in r["reasons"]:
            with st.expander(f"{reason.get('rule')} · {reason.get('message')}", expanded=True):
                st.write("Actual:", reason.get("actual_value"))
                st.write("Expected:", reason.get("expected_value"))
                if reason.get("matched_invoice_id"):
                    st.write("Matched invoice:", reason.get("matched_invoice_id"))
    st.markdown('<div class="section">Trusted evidence</div>', unsafe_allow_html=True)
    st.json(r.get("evidence") or {})


def copilot_page() -> None:
    st.markdown('<div class="copilot"><div class="eyebrow">FINSIGHT AI WORKSPACE</div><h2>Ask FinSight.</h2><p>Get clear explanations of invoice decisions, exception patterns, review routing, CSV checks, audit activity, and how the app works. Off-topic requests are intentionally outside scope.</p></div>', unsafe_allow_html=True)
    if not st.session_state.results:
        st.info("Upload and analyze a CSV first for invoice-specific answers. You can still ask how FinSight works.")
    quick = ["Summarize this batch", "Which invoices need review?", "Explain every exception", "Why is INV003 flagged?", "How does FinSight decide?"]
    cols = st.columns(len(quick))
    for c, prompt in zip(cols, quick):
        with c:
            if st.button(prompt, key="quick_"+prompt, width="stretch"):
                st.session_state.chat.append(("user", prompt))
                from src.copilot_workflow import copilot_workflow
                response = copilot_workflow(prompt, st.session_state.results, st.session_state.chat[:-1])
                st.session_state.chat.append(("assistant", response["answer"], response["mode"]))
                st.rerun()
    for item in st.session_state.chat:
        role = item[0]
        content = item[1]
        with st.chat_message(role):
            st.markdown(content)
            if role == "assistant" and len(item) > 2:
                st.caption(f"Source: {item[2]}")
    question = st.chat_input("Ask FinSight about this analysis…")
    if question:
        from src.copilot_workflow import copilot_workflow
        st.session_state.chat.append(("user", question))
        response = copilot_workflow(question, st.session_state.results, st.session_state.chat[:-1])
        st.session_state.chat.append(("assistant", response["answer"], response["mode"]))
        st.rerun()


def system_page() -> None:
    st.markdown('<div class="section">System health</div>', unsafe_allow_html=True)
    st.caption("These checks report the actual server-side configuration available to this Streamlit session.")
    try:
        from src.ai import test_gemini_connection
        gem_ok, gem_msg = test_gemini_connection()
    except Exception as exc:
        gem_ok, gem_msg = False, f"{type(exc).__name__}: {exc}"
    try:
        from src.persistence import test_supabase_connection
        sb_ok, sb_msg = test_supabase_connection()
    except Exception as exc:
        sb_ok, sb_msg = False, f"{type(exc).__name__}: {exc}"
    a,b = st.columns(2)
    with a:
        st.markdown(f'<div class="panel"><h3>Gemini</h3><p class="muted">{"Connected" if gem_ok else "Not connected"}</p><p class="muted">{gem_msg}</p></div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div class="panel"><h3>Supabase</h3><p class="muted">{"Connected" if sb_ok else "Not connected"}</p><p class="muted">{sb_msg}</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="section">Architecture</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel"><b>CSV → Python rule engine → trusted result → Copilot explanation</b><br><span class="muted">The AI layer cannot alter invoice status, route, confidence, rule IDs, or evidence.</span></div>',
        unsafe_allow_html=True,
    )
    if st.session_state.audit:
        st.markdown('<div class="section">Session audit</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(st.session_state.audit), width="stretch", hide_index=True)


def overview_page() -> None:
    hero()
    if st.session_state.df is None:
        st.markdown('<div class="section">One workspace. Four decisions.</div>', unsafe_allow_html=True)
        cols = st.columns(4)
        cards = [
            ("01","Validate","Schema, missing values, amounts, dates and categories."),
            ("02","Detect","Limits, duplicate IDs and possible duplicate invoices."),
            ("03","Review","Evidence-first queue for cases needing a human."),
            ("04","Explain","Copilot explains the deterministic result in plain language."),
        ]
        for c,(n,t,b) in zip(cols,cards):
            with c:
                st.markdown(f'<div class="feature"><div class="icon">{n}</div><h3>{t}</h3><p>{b}</p></div>',unsafe_allow_html=True)
        st.markdown('<div class="section">Start here</div>', unsafe_allow_html=True)
        if st.button("Load bundled sample →", type="primary"):
            reset_workspace(load_sample(), "data/invoices.csv")
            st.session_state.page = "Analyze"
            st.rerun()
        return
    st.markdown('<div class="section">Workspace snapshot</div>', unsafe_allow_html=True)
    if st.session_state.analyzed:
        metrics(st.session_state.results)
        st.markdown('<div class="panel"><b>Next:</b> open Analyze for the complete decision stream, Review for human actions, Evidence for rule-level proof, or Copilot for explanations.</div>', unsafe_allow_html=True)
    else:
        st.info(f"{st.session_state.source_name} is loaded with {len(st.session_state.df):,} rows. Open Analyze and run the deterministic engine.")


def main() -> None:
    init_state()
    sidebar()
    topbar()
    page = st.session_state.page
    if page == "Overview":
        overview_page()
    elif page == "Analyze":
        analysis_page()
    elif page == "Review":
        review_page()
    elif page == "Evidence":
        evidence_page()
    elif page == "Copilot":
        copilot_page()
    else:
        system_page()
    st.markdown('<div class="footer">FINSIGHT · DETERMINISTIC DECISIONS · HUMAN JUDGMENT · AI EXPLANATION</div>', unsafe_allow_html=True)


main()
