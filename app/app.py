"""FinSight AP Intelligence command center."""
from __future__ import annotations
from pathlib import Path
import sys
import pandas as pd
import streamlit as st

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from src.config import CATEGORY_LIMITS, REQUIRED_COLUMNS
from src.reporting import VIEWS, attach_reviews, filter_results, view_counts
from src.rule_engine import process_invoices, summarize_results

st.set_page_config(page_title="FinSight · AP Intelligence",page_icon="✨",layout="wide",initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#081325;--card:#111c2e;--card2:#152032;--card3:#202a3d;--line:#3c494d;--text:#d8e3fc;--muted:#bbc9ce;--cyan:#00d9ff;--blue:#adc6ff;--red:#ffb4ab}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:radial-gradient(circle at 85% -10%,rgba(0,217,255,.10),transparent 35%),var(--bg)!important;color:var(--text)!important}
body,[class*="css"]{font-family:Inter,sans-serif}[data-testid="stHeader"]{background:rgba(8,19,37,.85)!important;border-bottom:1px solid var(--line)}
.block-container{max-width:1500px;padding:26px 36px 70px}h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;color:var(--text)!important}
p,label,span,.stMarkdown{color:var(--text)}[data-testid="stSidebar"],[data-testid="stSidebar"]>div{background:#040e20!important;border-right:1px solid var(--line)!important}[data-testid="stSidebar"] *{color:var(--text)!important}
.hero,.card,.metric{border:1px solid var(--line);border-radius:18px;background:linear-gradient(135deg,var(--card),var(--card2));padding:22px;box-shadow:0 16px 45px rgba(0,0,0,.18)}
.hero{padding:36px;margin-bottom:20px}.hero h1{font-size:3.3rem;line-height:.98;margin:12px 0}.hero h1 span{color:var(--cyan)}.muted{color:var(--muted)!important}
.metric{padding:16px}.metric small{display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.metric strong{display:block;font:700 1.8rem 'Space Grotesk';margin-top:6px}.live,.badge{display:inline-block;border:1px solid rgba(0,217,255,.35);background:rgba(0,217,255,.08);border-radius:999px;padding:6px 10px;color:var(--cyan)!important;font:700 .7rem 'Space Grotesk';letter-spacing:.07em}
.stButton>button{border-radius:10px!important}.stTextInput>div>div,.stTextArea>div>div,.stSelectbox>div>div,input,textarea,[data-baseweb="select"]>div{background:var(--card2)!important;color:var(--text)!important;border-color:var(--line)!important}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden}[data-testid="stTabs"] [role="tab"]{color:var(--muted)!important}.stTabs [aria-selected="true"]{color:var(--cyan)!important}
[data-testid="stChatMessage"],[data-testid="stExpander"],[data-testid="stFileUploader"]{background:var(--card)!important;border:1px solid var(--line)!important;border-radius:14px!important}
.footer{text-align:center;color:#859398!important;font:600 .65rem 'Space Grotesk';letter-spacing:.15em;margin-top:40px}
</style>""",unsafe_allow_html=True)

def init_state():
    defaults={"df":None,"source_name":"","results":[],"analyzed":False,"audit":[],"reviews":{},"chat":[],"persist_note":"","conn":None}
    for k,v in defaults.items(): st.session_state.setdefault(k,v)

def reset_workspace(df=None,source_name=""):
    st.session_state.df=df; st.session_state.source_name=source_name; st.session_state.results=[]; st.session_state.analyzed=False
    st.session_state.audit=[]; st.session_state.reviews={}; st.session_state.chat=[]; st.session_state.persist_note=""

def load_sample(): return pd.read_csv(ROOT/"data"/"invoices.csv")

def add_audit(event,invoice_id="",message="",metadata=None,persist=True):
    record={"timestamp":pd.Timestamp.now(tz="UTC").isoformat(),"event":event,"invoice_id":str(invoice_id),"message":message}
    st.session_state.audit.append(record)
    if persist:
        try:
            from src.persistence import save_audit_event
            save_audit_event(event,invoice_id,message,metadata)
        except Exception: pass

def build_results_df(results):
    return pd.DataFrame([{"invoice_id":r.get("invoice_id"),"vendor":(r.get("evidence") or {}).get("vendor"),
        "amount":(r.get("evidence") or {}).get("amount"),"category":(r.get("evidence") or {}).get("category"),
        "invoice_date":(r.get("evidence") or {}).get("invoice_date"),"status":r.get("status"),"route":r.get("route"),
        "confidence":float(r.get("confidence",0)),"human_review_required":bool(r.get("human_review_required")),
        "rule_ids":", ".join(r.get("rule_ids") or []),"reasons":" | ".join(str(x.get("message","")) for x in r.get("reasons",[])),
        "matched_invoice_id":(r.get("evidence") or {}).get("matched_invoice_id")} for r in results])

def run_analysis():
    if st.session_state.df is None: st.warning("Load or upload an invoice CSV first."); return
    try:
        results=process_invoices(st.session_state.df); st.session_state.results=results; st.session_state.analyzed=True
        summary=summarize_results(results)
        batch=[{"event_type":"ANALYSIS_RUN","invoice_id":"","message":f"{st.session_state.source_name}: {summary['total']} invoices analyzed.","metadata":{"summary":summary}}]
        for r in results:
            batch.append({"event_type":"DECISION","invoice_id":r.get("invoice_id",""),"message":f"{r.get('status')} / {r.get('route')}",
                          "metadata":{"rule_ids":r.get("rule_ids",[]),"confidence":r.get("confidence"),"reasons":[x.get("message") for x in r.get("reasons",[])],"evidence":r.get("evidence")}})
        for e in batch: add_audit(e["event_type"],e["invoice_id"],e["message"],e["metadata"],False)
        try:
            from src.persistence import save_audit_events
            ok,note=save_audit_events(batch); st.session_state.persist_note=note if ok else f"Not persisted: {note}"
        except Exception as exc: st.session_state.persist_note=f"Not persisted: {exc}"
        st.toast(f"Analysis complete · {summary['total']} invoices",icon="✨")
    except Exception as exc:
        st.session_state.analyzed=False; st.error(f"Analysis failed: {exc}")

def render_metrics():
    s=summarize_results(st.session_state.results)
    avg=sum(float(r.get("confidence",0)) for r in st.session_state.results)/len(st.session_state.results) if st.session_state.results else 0
    cols=st.columns(5)
    for col,(label,value) in zip(cols,[("Invoices",s["total"]),("Auto-pass",s["clean"]),("Exceptions",s["exceptions"]),("Human review",s["review_required"]),("Confidence",f"{avg:.0%}")]):
        with col: st.markdown(f'<div class="metric"><small>{label}</small><strong>{value}</strong></div>',unsafe_allow_html=True)

def render_results():
    render_metrics(); out=attach_reviews(build_results_df(st.session_state.results),st.session_state.reviews)
    counts=view_counts(out); a,b=st.columns([3,2])
    with a: view=st.radio("Queue",list(VIEWS),horizontal=True,key="result_view",format_func=lambda v:f"{v} ({counts[v]})",label_visibility="collapsed")
    with b: query=st.text_input("Search",key="result_search",placeholder="Search invoice, vendor, rule…",label_visibility="collapsed")
    shown=filter_results(out,query,view)
    st.caption(f"Showing {len(shown)} of {len(out)} invoices")
    st.dataframe(shown[["invoice_id","vendor","amount","category","status","route","confidence","reviewer_decision"]],width="stretch",hide_index=True)
    exceptions=out[out.status=="EXCEPTION"].copy()
    if not exceptions.empty:
        st.markdown("### Exceptions"); st.dataframe(exceptions[["invoice_id","vendor","amount","category","rule_ids","reasons","route"]],width="stretch",hide_index=True)
    x,y,z=st.columns(3)
    with x: st.download_button("↓ Download analyzed CSV",out.to_csv(index=False).encode(),"finsight_analyzed.csv","text/csv",width="stretch")
    with y: st.download_button(f"↓ Download exceptions ({len(exceptions)})",exceptions.to_csv(index=False).encode(),"finsight_exceptions.csv","text/csv",width="stretch")
    with z: st.download_button("↓ Download original CSV",st.session_state.df.to_csv(index=False).encode(),"finsight_original.csv","text/csv",width="stretch")

def review_tab():
    items=[r for r in st.session_state.results if r.get("human_review_required")]
    if not items: st.success("No invoices currently require human review."); return
    st.info(f"{len(items)} invoice(s) require a human decision. AI cannot approve or reject them.")
    for r in items:
        iid=str(r.get("invoice_id")); old=st.session_state.reviews.get(iid,{})
        with st.container(border=True):
            st.markdown(f"#### {iid}"); st.write(" ".join(str(x.get("message","")) for x in r.get("reasons",[])))
            st.caption(f"Route: {r.get('route')} · Confidence: {float(r.get('confidence',0)):.0%}")
            with st.expander("Evidence"): st.json({"evidence":r.get("evidence"),"rule_ids":r.get("rule_ids"),"reasons":r.get("reasons")})
            note=st.text_area("Reviewer note",value=old.get("comment",""),key=f"review_note_{iid}")
            a,b=st.columns(2)
            with a:
                if st.button("Approve",key=f"approve_{iid}",width="stretch"):
                    st.session_state.reviews[iid]={"action":"APPROVED","comment":note.strip()}; add_audit("REVIEW_ACTION",iid,f"APPROVED: {note.strip()}"); st.success(f"{iid} marked APPROVED.")
            with b:
                if st.button("Reject",key=f"reject_{iid}",width="stretch"):
                    st.session_state.reviews[iid]={"action":"REJECTED","comment":note.strip()}; add_audit("REVIEW_ACTION",iid,f"REJECTED: {note.strip()}"); st.warning(f"{iid} marked REJECTED.")

def evidence_tab():
    ids=[str(r.get("invoice_id")) for r in st.session_state.results]
    selected=st.selectbox("Select invoice",ids,key="evidence_invoice")
    r=next(x for x in st.session_state.results if str(x.get("invoice_id"))==selected)
    st.markdown(f'<span class="badge">● {r.get("status")}</span> <span class="badge">{r.get("route")}</span>',unsafe_allow_html=True)
    a,b,c=st.columns(3); a.metric("Confidence",f"{float(r.get('confidence',0)):.0%}"); b.metric("Rule flags",len(r.get("rule_ids") or [])); c.metric("Human review","Required" if r.get("human_review_required") else "Not required")
    st.markdown("### Why this happened")
    if not r.get("reasons"): st.success("No rule violations. This invoice passed all configured checks.")
    for reason in r.get("reasons",[]):
        with st.expander(f"{reason.get('rule')} · {reason.get('message')}",expanded=True):
            st.write("Actual:",reason.get("actual_value")); st.write("Expected:",reason.get("expected_value"))
            if reason.get("matched_invoice_id"): st.write("Matched invoice:",reason.get("matched_invoice_id"))
    st.markdown("### Trusted evidence"); st.json(r.get("evidence") or {})

def copilot_tab():
    st.markdown("Ask FinSight about the loaded analysis. The assistant is intentionally limited to FinSight/AP/invoice/audit/application questions.")
    if not st.session_state.results: st.info("Analyze the CSV first for invoice-specific Copilot answers.")
    prompts=["Summarize this batch","Which invoices need review?","Explain every exception","Why is INV003 flagged?"]
    cols=st.columns(4)
    for col,prompt in zip(cols,prompts):
        with col:
            if st.button(prompt,key="quick_"+prompt,width="stretch"):
                from src.copilot_workflow import copilot_workflow
                st.session_state.chat.append(("user",prompt)); response=copilot_workflow(prompt,st.session_state.results,st.session_state.chat[:-1])
                st.session_state.chat.append(("assistant",response["answer"],response["mode"])); st.rerun()
    for item in st.session_state.chat:
        with st.chat_message(item[0]): st.markdown(item[1]); st.caption(f"Source: {item[2]}" if len(item)>2 else "")
    question=st.chat_input("Ask FinSight…")
    if question:
        from src.copilot_workflow import copilot_workflow
        st.session_state.chat.append(("user",question)); response=copilot_workflow(question,st.session_state.results,st.session_state.chat[:-1])
        st.session_state.chat.append(("assistant",response["answer"],response["mode"])); st.rerun()

def main():
    init_state()
    with st.sidebar:
        st.markdown("## ✦ FinSight"); st.caption("Accounts-payable intelligence")
        st.markdown('<span class="live">● RULE ENGINE ONLINE</span>',unsafe_allow_html=True); st.divider()
        st.markdown("**Required CSV columns**"); st.code("\n".join(REQUIRED_COLUMNS))
        st.markdown("**Configured limits**")
        for category,limit in CATEGORY_LIMITS.items(): st.caption(f"{category} · ₹{limit:,.0f}")
        st.divider()
        if st.button("Check connections",key="check_connections",width="stretch"):
            conn={}
            try:
                from src.ai import test_gemini_connection
                conn["Gemini"]=test_gemini_connection()
            except Exception as exc: conn["Gemini"]=(False,str(exc))
            try:
                from src.persistence import test_supabase_connection
                conn["Supabase"]=test_supabase_connection()
            except Exception as exc: conn["Supabase"]=(False,str(exc))
            st.session_state.conn=conn
        for name,(ok,msg) in (st.session_state.conn or {}).items(): (st.success if ok else st.warning)(f"{name}: {msg}")

    st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center"><h3>FINSIGHT <span style="color:#00d9ff">/ AP INTELLIGENCE</span></h3><span class="live">● {st.session_state.source_name or "NO DATASET LOADED"}</span></div>',unsafe_allow_html=True)
    st.markdown('<div class="hero"><div class="live">INVOICE CONTROL · EVIDENCE · HUMAN REVIEW</div><h1>Analyze every invoice.<br><span>See every decision.</span></h1><p>Upload a CSV, run the deterministic rule engine, inspect evidence, and send uncertain cases to human review.</p></div>',unsafe_allow_html=True)

    st.markdown("### 1 · Load your invoice data")
    upload_col,sample_col,reset_col=st.columns([5,1.5,1.2])
    with upload_col: uploaded=st.file_uploader("Invoice CSV",type=["csv"],key="invoice_upload",help="Required: invoice_id, vendor, amount, category, invoice_date")
    with sample_col:
        st.write(""); st.write("")
        if st.button("Load sample",key="load_sample",width="stretch"): reset_workspace(load_sample(),"data/invoices.csv"); st.rerun()
    with reset_col:
        st.write(""); st.write("")
        if st.button("Reset",key="reset_workspace",width="stretch"): reset_workspace(); st.rerun()
    if uploaded is not None and uploaded.name != st.session_state.source_name:
        try: reset_workspace(pd.read_csv(uploaded),uploaded.name); st.toast(f"{uploaded.name} loaded",icon="✨")
        except Exception as exc: st.error(f"Could not read CSV: {exc}")

    if st.session_state.df is None:
        st.markdown('<div class="card"><h3>Nothing loaded yet</h3><p class="muted">Load the bundled sample or upload your own CSV.</p></div>',unsafe_allow_html=True)
        return

    df=st.session_state.df; st.markdown("### 2 · Run the analysis")
    left,right=st.columns([4,1.5])
    with left: st.markdown(f'<div class="card"><b>{st.session_state.source_name}</b><br><span class="muted">{len(df):,} invoice rows loaded · {len(df.columns)} columns</span></div>',unsafe_allow_html=True)
    with right:
        if st.button("✦ ANALYZE INVOICES",key="analyze_btn",type="primary",width="stretch"): run_analysis(); st.rerun()
    st.markdown("### Source preview"); st.dataframe(df.head(100),width="stretch",hide_index=True)
    if not st.session_state.analyzed:
        st.markdown('<div class="card"><h3>Ready to analyze</h3><p class="muted">Press ANALYZE INVOICES above.</p></div>',unsafe_allow_html=True); return

    st.markdown("### 3 · Analysis results"); render_results()
    tabs=st.tabs(["Review queue","Evidence","Copilot","Audit & system"])
    with tabs[0]: review_tab()
    with tabs[1]: evidence_tab()
    with tabs[2]: copilot_tab()
    with tabs[3]:
        st.markdown("#### Session audit")
        if st.session_state.audit: st.dataframe(pd.DataFrame(st.session_state.audit),width="stretch",hide_index=True)
        else: st.info("No audit events in this session.")
        st.markdown("#### Configuration"); st.json({"required_columns":REQUIRED_COLUMNS,"category_limits":CATEGORY_LIMITS})
        if st.session_state.persist_note: st.caption(f"Audit persistence: {st.session_state.persist_note}")
        if st.button("Load persisted audit log",key="load_remote_audit"):
            from src.persistence import fetch_audit_events
            ok,data=fetch_audit_events(200)
            if ok: st.dataframe(pd.DataFrame(data),width="stretch",hide_index=True) if data else st.info("The persisted audit log is empty.")
            else: st.warning(data)
    st.markdown('<div class="footer">FINSIGHT · PYTHON RULE ENGINE IS THE SOURCE OF TRUTH · AI EXPLAINS, NEVER DECIDES</div>',unsafe_allow_html=True)

main()
