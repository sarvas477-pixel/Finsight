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
:root{--bg:#f7f8fc;--surface:#fff;--surface2:#f1f3f8;--line:#e5e7ef;--text:#171923;--muted:#687080;--pink:#e94f8a;--violet:#7357e8;--cyan:#159fc1;--green:#168a5a;--amber:#b97900}
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"],[data-testid="stToolbar"]{background:var(--bg)!important;color:var(--text)!important}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:radial-gradient(800px 420px at 88% -10%,rgba(115,87,232,.13),transparent 65%),radial-gradient(650px 380px at -8% 35%,rgba(233,79,138,.08),transparent 65%),var(--bg)!important}
.block-container{max-width:1480px;padding:30px 42px 70px}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;color:var(--text)!important}
p,label,span,small,.stMarkdown{color:var(--text)}
[data-testid="stSidebar"],[data-testid="stSidebar"]>div{background:rgba(255,255,255,.92)!important;border-right:1px solid var(--line)!important}
[data-testid="stSidebar"] *{color:var(--text)!important}.stCaption,[data-testid="stSidebar"] .stCaption{color:var(--muted)!important}hr{border-color:var(--line)!important}
.hero{position:relative;overflow:hidden;border:1px solid #e0e2eb;border-radius:30px;padding:42px;background:linear-gradient(135deg,#fff,#f5f2ff);box-shadow:0 24px 70px rgba(35,39,60,.10);isolation:isolate}
.hero:before{content:"";position:absolute;width:500px;height:500px;right:-200px;top:-270px;border-radius:50%;background:radial-gradient(circle,rgba(115,87,232,.22),transparent 67%);animation:glow 6s ease-in-out infinite;z-index:-1}
.hero:after{content:"";position:absolute;width:280px;height:280px;left:38%;bottom:-250px;border-radius:50%;background:rgba(233,79,138,.09);filter:blur(70px);z-index:-1}
.hero-grid{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:30px;align-items:center}
.eyebrow{color:var(--violet)!important;font-size:.70rem;font-weight:800;letter-spacing:.20em}
.hero h1{font-size:clamp(3.2rem,6vw,6.3rem);line-height:.86;letter-spacing:-.075em;margin:15px 0 20px}
.hero h1 span{background:linear-gradient(90deg,var(--pink),var(--violet),var(--cyan));-webkit-background-clip:text;color:transparent}
.hero p{max-width:700px;color:var(--muted)!important;font-size:1.05rem;line-height:1.7}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:24px}.chips span,.source-pill{border:1px solid #dfe2ea;background:#fff;border-radius:999px;padding:8px 12px;font-size:.74rem;color:#555d6c!important;box-shadow:0 3px 12px rgba(30,35,55,.04)}
.orb{height:290px;position:relative;display:grid;place-items:center}.orb-core{width:94px;height:94px;border-radius:28px;display:grid;place-items:center;background:linear-gradient(135deg,var(--pink),var(--violet));font-size:2rem;color:#fff!important;box-shadow:0 18px 50px rgba(115,87,232,.30);animation:float 4s ease-in-out infinite;z-index:2}.orb-ring{position:absolute;border:1px solid rgba(115,87,232,.22);border-radius:50%;animation:spin 13s linear infinite}.r1{width:180px;height:180px}.r2{width:275px;height:275px;border-color:rgba(21,159,193,.16);animation-duration:19s;animation-direction:reverse}
.section-title{font:700 1.65rem 'Space Grotesk';letter-spacing:-.04em;margin:34px 0 14px;color:var(--text)}
.feature,.panel,.copilot-hero,.metric{background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:22px;box-shadow:0 14px 42px rgba(35,39,60,.07)}
.feature{min-height:150px;padding:23px;transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease}.feature:hover{transform:translateY(-3px);border-color:#d1d4df;box-shadow:0 20px 50px rgba(35,39,60,.10)}
.feature-icon{font-size:1.45rem;color:var(--pink)!important}.feature h3{margin:12px 0 5px}.feature p,.copilot-hero p{color:var(--muted)!important;line-height:1.55}
.metric{padding:17px;min-height:92px}.metric small{display:block;color:var(--muted)!important;font-size:.70rem;text-transform:uppercase;letter-spacing:.12em}.metric strong{display:block;font:700 2rem 'Space Grotesk';margin-top:7px}.metric.safe strong{color:var(--green)}.metric.flagged strong{color:var(--pink)}.metric.attention strong{color:var(--amber)}.metric.score strong{color:var(--cyan)}
.copilot-hero{padding:28px;background:linear-gradient(135deg,#fff0f7,#f2efff)}.copilot-hero h2{font-size:3rem;margin:8px 0}.panel{padding:22px}.source-pill{display:inline-block;margin:18px 0}.footer{text-align:center;color:#969baa!important;font-size:.68rem;letter-spacing:.15em;margin-top:48px}
div.stButton>button,div.stDownloadButton>button{border-radius:13px!important;border:1px solid #d9dce5!important;background:#fff!important;color:#252938!important;min-height:44px!important;font-weight:700!important;transition:all .20s ease!important;box-shadow:0 3px 12px rgba(35,39,60,.05)!important}
div.stButton>button:hover,div.stDownloadButton>button:hover{border-color:var(--pink)!important;transform:translateY(-1px)!important;box-shadow:0 8px 22px rgba(35,39,60,.09)!important}
button[kind="primary"]{background:linear-gradient(100deg,var(--pink),var(--violet))!important;border:0!important;color:#fff!important;box-shadow:0 10px 28px rgba(115,87,232,.22)!important}
[data-testid="stFileUploader"],[data-testid="stFileUploader"] section,[data-testid="stFileUploader"] section>div{background:#fff!important;border:1px dashed #cfd3df!important;border-radius:18px!important}
[data-testid="stFileUploader"] button{background:#f4f5f8!important;color:#242837!important;border:1px solid #d8dbe4!important}[data-testid="stFileUploader"] small{color:#7b8290!important}
.stTextInput>div>div,.stTextArea>div>div,.stSelectbox>div>div,.stNumberInput>div>div,input,textarea,[data-baseweb="select"]>div{background:#fff!important;color:var(--text)!important;border-color:#d9dce5!important}
input::placeholder,textarea::placeholder{color:#9298a5!important}[data-baseweb="popover"],[data-baseweb="menu"]{background:#fff!important;color:var(--text)!important;border:1px solid var(--line)!important}[data-baseweb="menu"] *{color:var(--text)!important}
[data-testid="stExpander"]{background:#fff!important;border:1px solid var(--line)!important;border-radius:18px!important}[data-testid="stExpander"] summary{color:var(--text)!important}
[data-testid="stTabs"] [role="tab"]{color:#747b89!important;transition:color .2s ease}[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:var(--violet)!important}
[data-testid="stDataFrame"],[data-testid="stDataFrame"]>div{background:#fff!important;border:1px solid var(--line)!important;border-radius:16px!important;overflow:hidden}
[data-testid="stMetric"]{background:#fff!important;border:1px solid var(--line)!important;color:var(--text)!important;border-radius:18px!important}[data-testid="stMetricLabel"],[data-testid="stMetricValue"],[data-testid="stMetricDelta"]{color:var(--text)!important}
.stAlert{background:#fff!important;color:var(--text)!important;border:1px solid var(--line)!important}[data-testid="stChatMessage"]{background:#fff!important;border:1px solid var(--line)!important;border-radius:18px!important;margin-bottom:8px}[data-testid="stChatInput"]{background:#fff!important;border-color:#d5d9e3!important}[data-testid="stChatInput"] textarea{background:#fff!important}
[data-testid="stSpinner"]{color:var(--violet)!important}::selection{background:rgba(115,87,232,.18)}
@keyframes glow{50%{transform:scale(1.10);opacity:.72}}@keyframes float{50%{transform:translateY(-10px) rotate(3deg)}}@keyframes spin{to{transform:rotate(360deg)}}
@media(max-width:900px){.block-container{padding:20px 16px 50px}.hero{padding:28px}.hero-grid{grid-template-columns:1fr}.orb{height:180px}.hero h1{font-size:3.6rem}}
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
    from src.copilot_workflow import analyze_invoice_workflow
    return analyze_invoice_workflow(df)["results"]


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


def copilot(question: str) -> tuple[str, str]:
    try:
        from src.copilot_workflow import copilot_workflow
        response = copilot_workflow(
            question,
            st.session_state.results,
            st.session_state.chat,
        )
        return response["answer"], response["mode"]
    except Exception as exc:
        return f"Copilot fallback is active ({type(exc).__name__}).", "fallback"


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
        st.markdown("### ✦ FinSight")
        st.caption("Invoice intelligence, without the spreadsheet headache.")
        uploaded = st.file_uploader("Drop your invoice CSV", type=["csv"])
        if uploaded is not None and uploaded.name != st.session_state.source_name:
            try:
                reset_workspace(pd.read_csv(uploaded), uploaded.name)
                st.toast("CSV loaded", icon="✦")
            except Exception as exc:
                st.error(f"Could not read CSV: {exc}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sample", use_container_width=True):
                try:
                    reset_workspace(load_sample(), "data/invoices.csv")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with c2:
            if st.button("Reset", use_container_width=True):
                reset_workspace()
                st.rerun()
        st.divider()
        st.caption("Required columns")
        st.code("invoice_id  vendor  amount  category  invoice_date", language="text")
        st.caption("Category limits")
        for category, limit in CATEGORY_LIMITS.items():
            st.write(f"{category} · ₹{limit:,.0f}")


def hero() -> None:
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">FINANCE OPS · AI-ASSISTED</div>
      <div class="hero-grid">
        <div>
          <h1>Make the<br><span>exception pile</span><br>disappear.</h1>
          <p>Upload invoices. Find problems. Understand why. Let humans decide what needs a second look.</p>
          <div class="chips"><span>Deterministic rules</span><span>Human-in-the-loop</span><span>AI Copilot</span></div>
        </div>
        <div class="orb"><div class="orb-core">✦</div><div class="orb-ring r1"></div><div class="orb-ring r2"></div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def empty_state() -> None:
    st.markdown('<div class="section-title">Ready when you are</div>', unsafe_allow_html=True)
    a,b,c = st.columns(3)
    for col, icon, title, body in [
        (a,"⌁","Drop a CSV","Your invoice data stays in the workspace."),
        (b,"◈","Run analysis","Rules flag limits, duplicates and missing data."),
        (c,"✦","Ask Copilot","Get answers about FinSight or general topics."),
    ]:
        with col:
            st.markdown(f'<div class="feature"><div class="feature-icon">{icon}</div><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">FinSight Copilot</div>', unsafe_allow_html=True)
    copilot_tab()


def summary(results: list[dict]) -> None:
    s = summarize_results(results)
    avg = sum(float(x.get("confidence", 0)) for x in results) / max(len(results),1)
    # Exception status and human-review routing are separate concepts.
    exception_count = sum(str(x.get("status", "")).upper() == "EXCEPTION" for x in results)
    review_count = sum(bool(x.get("human_review_required")) for x in results)
    vals = [
        ("Invoices", s["total"], "total"),
        ("Auto-pass", s["clean"], "safe"),
        ("Exceptions", exception_count, "flagged"),
        ("Human review", review_count, "attention"),
        ("Confidence", f"{avg:.0%}", "score"),
    ]
    cols = st.columns(5)
    for col,(label,value,kind) in zip(cols, vals):
        with col:
            st.markdown(f'<div class="metric {kind}"><small>{label}</small><strong>{value}</strong></div>', unsafe_allow_html=True)


def results_section(df: pd.DataFrame, results: list[dict]) -> None:
    st.markdown('<div class="section-title">Your analysis</div>', unsafe_allow_html=True)
    summary(results)
    out = build_results_df(results)
    exceptions = out[out["status"] == "EXCEPTION"].copy()

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("#### Decision stream")
    st.caption("The rule engine is the source of truth. AI explains; it does not change decisions.")
    show = out[["invoice_id","vendor","amount","category","status","route","confidence"]].copy()
    st.dataframe(show, use_container_width=True, hide_index=True,
                 column_config={"confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1, format="%.0f%%")})
    st.markdown("</div>", unsafe_allow_html=True)

    if not exceptions.empty:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### Exception details")
        st.caption("These are the rows that failed one or more configured validation rules.")
        exception_show = exceptions[
            ["invoice_id", "vendor", "amount", "category", "status", "route", "rule_ids", "reasons"]
        ].copy()
        st.dataframe(exception_show, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    x,y,z = st.columns(3)
    with x:
        st.download_button("↓ Analyzed CSV", out.to_csv(index=False).encode(), "finsight_analyzed.csv", "text/csv", use_container_width=True)
    with y:
        st.download_button(f"↓ Exceptions ({len(exceptions)})", exceptions.to_csv(index=False).encode(), "finsight_exceptions.csv", "text/csv", use_container_width=True)
    with z:
        st.download_button("↓ Original CSV", df.to_csv(index=False).encode(), "finsight_original.csv", "text/csv", use_container_width=True)

    st.markdown('<div class="section-title">Exception queue</div>', unsafe_allow_html=True)
    st.caption("Every invoice with status EXCEPTION is shown here, including exceptions that require human review.")

    view = st.radio(
        "Show",
        ["All", "Exceptions only", "Clean only"],
        horizontal=True,
        label_visibility="collapsed",
        key="results_view",
    )
    if view == "Exceptions only":
        visible = [x for x in results if str(x.get("status", "")).upper() == "EXCEPTION"]
    elif view == "Clean only":
        visible = [x for x in results if str(x.get("status", "")).upper() == "CLEAN"]
    else:
        visible = results

    flagged = [x for x in results if str(x.get("status", "")).upper() == "EXCEPTION"]
    if not flagged:
        st.success("Everything passed the configured checks.")
    elif view == "Exceptions only":
        st.success(f"{len(flagged)} exception(s) detected.")
    for item in visible[:50]:
        with st.container(border=True):
            a,b = st.columns([5,1])
            with a:
                st.markdown(f"### {item.get('invoice_id')} · {item.get('status')}")
                st.write(explain(item))
                st.caption(" · ".join(item.get("rule_ids") or []) or "No rule IDs")
            with b:
                st.metric("Confidence", f"{float(item.get('confidence',0)):.0%}")


def review_tab(results: list[dict]) -> None:
    items = [x for x in results if x.get("human_review_required")]
    st.markdown('<div class="section-title">Human review</div>', unsafe_allow_html=True)
    if not items:
        st.success("No invoices currently require human review.")
        return
    for item in items:
        iid = str(item.get("invoice_id"))
        old = st.session_state.reviews.get(iid, {})
        with st.container(border=True):
            st.markdown(f"### {iid}")
            st.write(explain(item))
            note = st.text_area("Reviewer note", value=old.get("comment",""), key=f"note_{iid}")
            a,b = st.columns(2)
            with a:
                if st.button("Approve", key=f"approve_{iid}", use_container_width=True):
                    record_review(iid, "APPROVED", note); st.success(f"{iid} approved.")
            with b:
                if st.button("Reject", key=f"reject_{iid}", use_container_width=True):
                    record_review(iid, "REJECTED", note); st.warning(f"{iid} rejected.")


def evidence_tab(results: list[dict]) -> None:
    st.markdown('<div class="section-title">Evidence</div>', unsafe_allow_html=True)
    ids = [str(x.get("invoice_id")) for x in results]
    selected = st.selectbox("Invoice", ids)
    item = next(x for x in results if str(x.get("invoice_id")) == selected)
    a,b,c = st.columns(3)
    a.metric("Status", item.get("status","—")); b.metric("Route", item.get("route","—")); c.metric("Confidence", f"{float(item.get('confidence',0)):.0%}")
    st.markdown("#### Why this decision?")
    st.write(explain(item))
    x,y = st.columns(2)
    with x: st.markdown("**Trusted evidence**"); st.json(item.get("evidence", {}))
    with y: st.markdown("**Triggered rules**"); st.json(item.get("reasons", []))


def audit_tab(results: list[dict]) -> None:
    st.markdown('<div class="section-title">Activity</div>', unsafe_allow_html=True)
    audit_df = pd.DataFrame(st.session_state.audit)
    if audit_df.empty:
        st.info("No activity yet.")
    else:
        st.dataframe(audit_df, use_container_width=True, hide_index=True)
    out = build_results_df(results)
    exceptions = out[out["status"] == "EXCEPTION"]
    a,b = st.columns(2)
    with a: st.download_button("Audit JSON", json.dumps(st.session_state.audit, indent=2, default=str).encode(), "finsight_audit.json", "application/json", use_container_width=True)
    with b: st.download_button("Analyzed CSV", out.to_csv(index=False).encode(), "finsight_analyzed.csv", "text/csv", use_container_width=True)
    if st.button("Check connections", use_container_width=True):
        try:
            from src.ai import test_gemini_connection
            ok,msg = test_gemini_connection(); (st.success if ok else st.warning)(f"Gemini: {msg}")
        except Exception as exc: st.warning(f"Gemini check unavailable: {exc}")
        try:
            from src.persistence import test_supabase_connection
            ok,msg = test_supabase_connection(); (st.success if ok else st.warning)(f"Supabase: {msg}")
        except Exception as exc: st.warning(f"Supabase check unavailable: {exc}")


def copilot_tab() -> None:
    st.markdown('<div class="section-title">✦ FinSight Copilot</div>', unsafe_allow_html=True)
    st.markdown('<div class="copilot-hero"><span class="eyebrow">YOUR AI WORKSPACE</span><h2>Ask anything.</h2><p>Invoices, coding, study, science, writing, ideas — or anything else. Invoice decisions remain controlled by the rule engine.</p></div>', unsafe_allow_html=True)
    prompts = ["Summarize this batch","Which invoices need review?","Explain the exceptions","Explain Python simply"]
    cols = st.columns(4)
    for col,prompt in zip(cols,prompts):
        with col:
            if st.button(prompt, key=f"quick_{prompt}", use_container_width=True):
                answer,mode = copilot(prompt)
                st.session_state.chat += [("user",prompt),("assistant",answer)]
                add_audit("AI_QUERY","",f"{mode}: {prompt}")
                st.rerun()
    for role,message in st.session_state.chat:
        with st.chat_message(role):
            st.write(message)
    question = st.chat_input("Ask FinSight Copilot anything…")
    if question:
        with st.spinner("Thinking…"):
            answer,mode = copilot(question)
        st.session_state.chat += [("user",question),("assistant",answer)]
        add_audit("AI_QUERY","",f"{mode}: {question}")
        st.rerun()


def workspace() -> None:
    df = st.session_state.df
    st.markdown(f'<div class="source-pill">● {st.session_state.source_name} · {len(df):,} invoices loaded</div>', unsafe_allow_html=True)
    a,b = st.columns([1,3])
    with a:
        run = st.button("✦ Analyze invoices", type="primary", use_container_width=True)
    with b:
        st.caption("Results appear below instantly. Your CSV is never used to change the rule engine.")
    with st.expander("Preview CSV"):
        st.dataframe(df.head(100), use_container_width=True, hide_index=True)
    if run:
        try:
            with st.spinner("Scanning invoices…"):
                results = analyze(df)
            st.session_state.results = results
            st.session_state.analyzed = True
            st.session_state.audit = []
            st.session_state.reviews = {}
            st.session_state.chat = []
            for item in results:
                add_audit("DECISION", str(item.get("invoice_id")),
                          f"{item.get('status')} / {item.get('route')} / {float(item.get('confidence',0)):.0%}",
                          {"rule_ids": item.get("rule_ids", [])})
            st.success(f"Analysis complete · {len(results):,} invoices checked")
        except Exception as exc:
            st.error(f"Analysis failed safely: {exc}")
            return
    if not st.session_state.analyzed:
        st.info("Click Analyze invoices to start.")
        return
    results_section(df, st.session_state.results)
    tabs = st.tabs(["Review","Evidence","Activity","✦ Copilot"])
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
st.markdown('<div class="footer">FINSIGHT · AP INTELLIGENCE · RULES + HUMAN JUDGMENT + AI</div>', unsafe_allow_html=True)
