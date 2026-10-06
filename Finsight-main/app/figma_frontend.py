"""FinSight — bright Figma-inspired frontend."""
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

st.set_page_config(page_title="FinSight · AP Intelligence", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#f5f7fb;--card:#fff;--ink:#121826;--muted:#667085;--line:#e6eaf0;--blue:#2857e8;--blue-soft:#edf2ff}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:var(--bg)!important;color:var(--ink)!important}
body,[class*="css"]{font-family:Inter,sans-serif}h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;color:var(--ink)!important}
.block-container{max-width:1500px;padding:28px 34px 70px}[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid var(--line)}
[data-testid="stSidebar"] *{color:var(--ink)!important}.brand{font:700 27px 'Space Grotesk';color:#2857e8!important}.muted{color:#667085!important}
.hero{background:linear-gradient(135deg,#fff,#f0f4ff);border:1px solid var(--line);border-radius:24px;padding:32px 34px;margin:10px 0 22px;box-shadow:0 14px 40px rgba(31,51,90,.07)}
.hero h1{font-size:42px;line-height:1.05;margin:8px 0 12px;letter-spacing:-.04em}.hero h1 span{color:#2857e8}.eyebrow{font-size:11px;font-weight:700;letter-spacing:.14em;color:#2857e8;text-transform:uppercase}
.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:0 8px 28px rgba(31,51,90,.05)}
.metric{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 20px;min-height:108px;box-shadow:0 6px 20px rgba(31,51,90,.04)}
.metric small{display:block;color:#667085;font-size:12px;font-weight:600}.metric strong{display:block;color:#121826;font:700 30px 'Space Grotesk';margin-top:7px}
.step{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;text-align:center}.step.active{background:#edf2ff;border-color:#cbd6ff;color:#2857e8}
.stButton>button{border-radius:10px!important;border:1px solid var(--line)!important;font-weight:600!important}.stButton>button[kind="primary"]{background:#2857e8!important;color:#fff!important;border-color:#2857e8!important}
.stTextInput>div>div,.stTextArea>div>div,[data-baseweb="select"]>div{background:#fff!important;border-color:var(--line)!important}
[data-testid="stFileUploader"]{background:#fff!important;border:1px dashed #b9c4d6!important;border-radius:16px!important}[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden}
[data-testid="stTabs"] [role="tab"]{color:#667085!important;font-weight:600}.stTabs [aria-selected="true"]{color:#2857e8!important}
.badge{display:inline-block;padding:5px 9px;border-radius:999px;background:#edf2ff;color:#2857e8;font-size:11px;font-weight:700;margin-right:6px}.footer{text-align:center;color:#98a2b3;font-size:11px;font-weight:600;letter-spacing:.12em;margin-top:36px}
</style>
""", unsafe_allow_html=True)

def init_state():
    for key,value in {"df":None,"source":"","results":[],"chat":[],"reviews":{},"audit":[]}.items():
        st.session_state.setdefault(key,value)

def reset(df=None,source=""):
    st.session_state.df=df;st.session_state.source=source;st.session_state.results=[];st.session_state.chat=[];st.session_state.reviews={};st.session_state.audit=[]

def result_frame(results):
    return pd.DataFrame([{"invoice_id":r.get("invoice_id"),"vendor":(r.get("evidence") or {}).get("vendor"),"amount":(r.get("evidence") or {}).get("amount"),"category":(r.get("evidence") or {}).get("category"),"invoice_date":(r.get("evidence") or {}).get("invoice_date"),"status":r.get("status"),"route":r.get("route"),"confidence":float(r.get("confidence",0)),"human_review_required":bool(r.get("human_review_required",False)),"dl_anomaly_score":r.get("dl_anomaly_score"),"ai_risk_score":float(r.get("ai_risk_score",0)),"rule_ids":", ".join(r.get("rule_ids") or []),"reasons":" | ".join(str(x.get("message","")) for x in r.get("reasons",[]))} for r in results])

def analyze():
    if st.session_state.df is None:return
    try:
        st.session_state.results=process_invoices(st.session_state.df)
        st.session_state.audit.append({"event":"ANALYSIS_RUN","source":st.session_state.source,"invoices":len(st.session_state.results),"timestamp":pd.Timestamp.now().isoformat()})
        st.toast("Analysis complete",icon="✦")
    except Exception as exc:st.error(f"Analysis failed: {exc}")

def metrics():
    s=summarize_results(st.session_state.results)
    avg=sum(float(r.get("confidence",0)) for r in st.session_state.results)/len(st.session_state.results) if st.session_state.results else 0
    cols=st.columns(5)
    for col,(label,value) in zip(cols,[("Total invoices",s["total"]),("Auto-passed",s["clean"]),("Exceptions",s["exceptions"]),("Human review",s["review_required"]),("Confidence",f"{avg:.0%}")]):
        with col:st.markdown(f'<div class="metric"><small>{label}</small><strong>{value}</strong></div>',unsafe_allow_html=True)

def ask_copilot(question):
    try:
        from src.copilot_workflow import copilot_workflow
        st.session_state.chat.append(("user",question))
        response=copilot_workflow(question,st.session_state.results,st.session_state.chat[:-1])
        st.session_state.chat.append(("assistant",response.get("answer","")));st.rerun()
    except Exception as exc:st.error(f"Copilot unavailable: {exc}")

def copilot():
    st.markdown("#### FinSight Copilot");st.caption("Ask about the current analysis. The rule engine remains the source of truth.")
    cols=st.columns(4)
    for col,p in zip(cols,["Show all exceptions","Graph the whole result","Show vendor names","Explain the flagged invoices"]):
        with col:
            if st.button(p,key="p_"+p,width="stretch"):ask_copilot(p)
    for item in st.session_state.chat:
        with st.chat_message(item[0]):st.markdown(item[1])
    q=st.chat_input("Ask FinSight…")
    if q:ask_copilot(q)

def main():
    init_state()
    with st.sidebar:
        st.markdown('<div class="brand">FinSight</div>',unsafe_allow_html=True);st.caption("AI-powered invoice intelligence");st.divider();st.markdown("**Workspace**")
        for label in ["Dashboard","Invoices","Exceptions","Audit Log","Copilot"]:
            bg="#edf2ff" if label=="Dashboard" else "#fff";color="#2857e8" if label=="Dashboard" else "#667085"
            st.markdown('<div style="padding:9px 10px;border-radius:9px;background:'+bg+';color:'+color+';font-weight:600">'+label+'</div>',unsafe_allow_html=True)
        st.divider();st.markdown("**Required CSV columns**");st.code("\n".join(REQUIRED_COLUMNS));st.markdown("**Category limits**")
        for category,limit in CATEGORY_LIMITS.items():st.caption(f"{category} · ₹{limit:,.0f}")

    st.markdown('<div class="eyebrow">INVOICE CONTROL · EVIDENCE · HUMAN REVIEW</div>',unsafe_allow_html=True)
    st.markdown('<div class="hero"><div class="eyebrow">FINSIGHT / AP INTELLIGENCE</div><h1>Analyze every invoice.<br><span>See every decision.</span></h1><p class="muted">Upload a CSV, run deterministic validation, review exceptions, and use Copilot to understand the results.</p></div>',unsafe_allow_html=True)

    st.markdown("### 1 · Upload invoice data");up,sample,clear=st.columns([6,1.4,1])
    with up:uploaded=st.file_uploader("Invoice CSV",type=["csv"],label_visibility="collapsed")
    with sample:
        if st.button("Load sample",width="stretch"):
            reset(pd.read_csv(ROOT/"data"/"invoices.csv"),"data/invoices.csv");st.rerun()
    with clear:
        if st.button("Reset",width="stretch"):reset();st.rerun()
    if uploaded is not None and uploaded.name!=st.session_state.source:
        try:reset(pd.read_csv(uploaded),uploaded.name)
        except Exception as exc:st.error(f"Could not read CSV: {exc}")

    if st.session_state.df is None:
        st.markdown('<div class="card"><b>Ready when you are.</b><br><span class="muted">Upload an invoice CSV or load the bundled sample to begin.</span></div>',unsafe_allow_html=True);st.markdown("### Copilot");copilot();return

    st.markdown("### 2 · Validate");a,b=st.columns([5,1.3])
    with a:st.markdown(f'<div class="card"><b>{st.session_state.source}</b><br><span class="muted">{len(st.session_state.df):,} invoice rows · {len(st.session_state.df.columns)} columns</span></div>',unsafe_allow_html=True)
    with b:
        if st.button("✦ Analyze CSV",type="primary",width="stretch"):analyze();st.rerun()
    st.markdown("#### Source preview");st.dataframe(st.session_state.df.head(100),width="stretch",hide_index=True)

    if not st.session_state.results:
        st.markdown('<div class="card"><b>Ready to analyze</b><br><span class="muted">The rule engine will validate vendor, amount, date, category limits, duplicates, and configured rules.</span></div>',unsafe_allow_html=True);return

    st.markdown("### 3 · Analysis results");metrics();out=result_frame(st.session_state.results)
    exceptions=out[out["status"]=="EXCEPTION"].copy();review=out[out["human_review_required"]==True].copy()
    st.markdown("#### Result table");query=st.text_input("Search results",placeholder="Search invoice, vendor, category or rule…",label_visibility="collapsed");shown=out
    if query:shown=out[out.astype(str).apply(lambda c:c.str.contains(query,case=False,na=False)).any(axis=1)]
    st.dataframe(shown[["invoice_id","vendor","amount","category","status","route","confidence","human_review_required"]],width="stretch",hide_index=True)
    x,y,z=st.columns(3)
    with x:st.download_button("↓ Download analyzed CSV",out.to_csv(index=False).encode(),"finsight_analyzed.csv","text/csv",width="stretch")
    with y:st.download_button(f"↓ Download exceptions ({len(exceptions)})",exceptions.to_csv(index=False).encode(),"finsight_exceptions.csv","text/csv",width="stretch")
    with z:st.download_button("↓ Download original CSV",st.session_state.df.to_csv(index=False).encode(),"finsight_original.csv","text/csv",width="stretch")

    st.markdown("### 4 · Workflow")
    for col,label,active in zip(st.columns(4),["Upload","Validate","Human Review","Audit"],[True,True,len(review)>0,bool(st.session_state.audit)]):
        with col:
            cls="step active" if active else "step";status="Complete" if active else "Waiting"
            st.markdown('<div class="'+cls+'"><b>'+label+'</b><br><span class="muted">'+status+'</span></div>',unsafe_allow_html=True)

    tabs=st.tabs(["Exceptions","Human Review","Evidence","Copilot","Audit Log"])
    with tabs[0]:
        if exceptions.empty:st.success("No exceptions found.")
        else:st.dataframe(exceptions[["invoice_id","vendor","amount","category","rule_ids","reasons","route"]],width="stretch",hide_index=True)
    with tabs[1]:
        if review.empty:st.success("No invoices currently require human review.")
        else:
            for _,row in review.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['invoice_id']}** · {row['route']}")
                    st.write(row["reasons"] or "Review required.");note=st.text_input("Reviewer note",key=f"note_{row['invoice_id']}")
                    c1,c2=st.columns(2)
                    with c1:
                        if st.button("Approve",key=f"approve_{row['invoice_id']}",width="stretch"):st.session_state.reviews[str(row["invoice_id"])]="APPROVED";st.success("Marked approved.")
                    with c2:
                        if st.button("Reject",key=f"reject_{row['invoice_id']}",width="stretch"):st.session_state.reviews[str(row["invoice_id"])]="REJECTED";st.warning("Marked rejected.")
    with tabs[2]:
        ids=out["invoice_id"].astype(str).tolist();selected=st.selectbox("Invoice",ids);raw=next(r for r in st.session_state.results if str(r.get("invoice_id"))==selected)
        st.markdown(f'<span class="badge">{raw.get("status")}</span><span class="badge">{raw.get("route")}</span>',unsafe_allow_html=True)
        c1,c2,c3=st.columns(3);c1.metric("Rule confidence",f"{float(raw.get('confidence',0)):.0%}");c2.metric("DL anomaly",f"{float(raw.get('dl_anomaly_score') or 0):.0%}");c3.metric("AI risk",f"{float(raw.get('ai_risk_score',0)):.0%}")
        st.markdown("**Why this happened**")
        for reason in raw.get("reasons",[]):st.warning(f"{reason.get('rule')}: {reason.get('message')}")
        st.json(raw.get("evidence") or {})
    with tabs[3]:copilot()
    with tabs[4]:
        if st.session_state.audit:st.dataframe(pd.DataFrame(st.session_state.audit),width="stretch",hide_index=True)
        else:st.info("No audit events in this session.")
    st.markdown('<div class="footer">FINSIGHT · RULE ENGINE IS THE SOURCE OF TRUTH · AI EXPLAINS, NEVER DECIDES</div>',unsafe_allow_html=True)

if __name__=="__main__":main()
