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
:root{--bg:#09090b;--panel:#121216;--panel2:#18181e;--text:#f6f5f2;--muted:#96959f;--line:#292932;--pink:#ff4f8b;--violet:#8b5cf6;--cyan:#42d9ff;--green:#39d98a;--amber:#ffc857}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:radial-gradient(circle at 75% 5%,#251238 0,#09090b 35%);color:var(--text)}
.block-container{max-width:1450px;padding:34px 42px 80px}
.stMarkdown,p,label,small{color:var(--text)}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important}
[data-testid="stSidebar"]{background:#0e0e12;border-right:1px solid var(--line)}
[data-testid="stSidebar"] *{color:#eee}
.hero{border:1px solid #302b3b;background:linear-gradient(135deg,#15131b,#101015);border-radius:32px;padding:42px;overflow:hidden;position:relative;box-shadow:0 30px 90px rgba(0,0,0,.35)}
.hero:before{content:"";position:absolute;width:480px;height:480px;right:-160px;top:-240px;border-radius:50%;background:radial-gradient(circle,#8b5cf655,transparent 65%);animation:pulse 5s ease-in-out infinite}
.hero-grid{display:grid;grid-template-columns:1fr 360px;gap:30px;align-items:center}.eyebrow{color:#ff78a6;font-size:.72rem;font-weight:800;letter-spacing:.18em}
.hero h1{font-size:clamp(3rem,6vw,6.5rem);line-height:.86;letter-spacing:-.075em;margin:15px 0}.hero h1 span{background:linear-gradient(90deg,#ff4f8b,#9b7bff,#42d9ff);-webkit-background-clip:text;color:transparent}
.hero p{max-width:720px;color:#aaa8b2;font-size:1.05rem;line-height:1.7}.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:24px}.chips span,.source-pill{border:1px solid #34343e;background:#17171d;border-radius:999px;padding:8px 12px;font-size:.75rem;color:#c9c7cf}
.orb{height:310px;position:relative;display:grid;place-items:center}.orb-core{width:100px;height:100px;border-radius:30px;display:grid;place-items:center;background:linear-gradient(135deg,#ff4f8b,#8b5cf6);font-size:2.2rem;box-shadow:0 0 70px #9b5cff88;animation:float 4s ease-in-out infinite;z-index:2}.orb-ring{position:absolute;border:1px solid #8b5cf655;border-radius:50%;animation:spin 12s linear infinite}.r1{width:190px;height:190px}.r2{width:290px;height:290px;border-color:#42d9ff33;animation-duration:18s;animation-direction:reverse}
.section-title{font:700 1.7rem 'Space Grotesk';letter-spacing:-.04em;margin:34px 0 14px}.feature,.panel,.copilot-hero{background:rgba(18,18,22,.88);border:1px solid var(--line);border-radius:24px;padding:24px;box-shadow:0 18px 55px rgba(0,0,0,.18)}.feature{min-height:155px}.feature-icon{font-size:1.5rem;color:#ff6b9b}.feature h3{margin:12px 0 5px}.feature p,.copilot-hero p{color:var(--muted);line-height:1.55}.metric{background:linear-gradient(145deg,#15151b,#101014);border:1px solid var(--line);border-radius:20px;padding:18px;min-height:95px}.metric small{display:block;color:#92909b;font-size:.72rem;text-transform:uppercase;letter-spacing:.12em}.metric strong{display:block;font:700 2rem 'Space Grotesk';margin-top:8px}.metric.safe strong{color:var(--green)}.metric.flagged strong{color:var(--pink)}.metric.attention strong{color:var(--amber)}.metric.score strong{color:var(--cyan)}
.copilot-hero{background:linear-gradient(135deg,#1a1220,#11131c)}.copilot-hero h2{font-size:3rem;margin:8px 0}.source-pill{display:inline-block;margin:20px 0}.footer{text-align:center;color:#666;font-size:.7rem;letter-spacing:.15em;margin-top:50px}
div.stButton>button,div.stDownloadButton>button{border-radius:14px;border:1px solid #33333d;background:#17171d;color:#f5f4f2;min-height:44px;font-weight:700;transition:.2s}div.stButton>button:hover,div.stDownloadButton>button:hover{border-color:#ff4f8b;transform:translateY(-1px)}
button[kind="primary"]{background:linear-gradient(90deg,#ff4f8b,#8b5cf6)!important;border:0!important;color:white!important;box-shadow:0 8px 30px #8b5cf633}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:18px;overflow:hidden}
@keyframes pulse{50%{transform:scale(1.12);opacity:.75}} @keyframes float{50%{transform:translateY(-12px) rotate(4deg)}} @keyframes spin{to{transform:rotate(360deg)}}
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


def copilot(question: str) -> tuple[str, str]:
    try:
        from src.ai import ask_gemini
        return ask_gemini(question, st.session_state.results, st.session_state.chat)
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
    vals = [
        ("Invoices", s["total"], "total"),
        ("Auto-pass", s["clean"], "safe"),
        ("Exceptions", s["exceptions"], "flagged"),
        ("Human review", s["review_required"], "attention"),
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

    x,y,z = st.columns(3)
    with x:
        st.download_button("↓ Analyzed CSV", out.to_csv(index=False).encode(), "finsight_analyzed.csv", "text/csv", use_container_width=True)
    with y:
        st.download_button(f"↓ Exceptions ({len(exceptions)})", exceptions.to_csv(index=False).encode(), "finsight_exceptions.csv", "text/csv", use_container_width=True)
    with z:
        st.download_button("↓ Original CSV", df.to_csv(index=False).encode(), "finsight_original.csv", "text/csv", use_container_width=True)

    st.markdown('<div class="section-title">Flagged invoices</div>', unsafe_allow_html=True)
    flagged = [x for x in results if x.get("status") != "CLEAN"]
    if not flagged:
        st.success("Everything passed the configured checks.")
    for item in flagged[:20]:
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
