from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

from src.config import REQUIRED_COLUMNS
from src.invoice_pipeline import process_invoice_dataframe

st.set_page_config(
    page_title="FinSight // Control Center",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { --bg:#070b14; --panel:#0d1422; --panel2:#111b2d; --line:#20304a; --text:#e7eefb; --muted:#8292ad; --cyan:#29e6d0; --blue:#5b8cff; --orange:#ffb454; --red:#ff6384; }
html,body,[class*="css"] { font-family:'Space Grotesk',sans-serif; }
.stApp { background: radial-gradient(circle at 80% -10%,#14284c 0,transparent 38%), var(--bg); color:var(--text); }
[data-testid="stSidebar"] { background:#080e1a; border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:var(--text); }
h1,h2,h3 { letter-spacing:-.04em; }
.hero { padding:26px 30px; border:1px solid #254067; border-radius:18px; background:linear-gradient(120deg,rgba(16,31,55,.98),rgba(11,22,37,.92)); box-shadow:0 18px 60px #0006; position:relative; overflow:hidden; }
.hero:after { content:'◈'; position:absolute; right:35px; top:-24px; font-size:170px; color:#29e6d008; transform:rotate(18deg); }
.eyebrow { color:var(--cyan); font:500 11px 'DM Mono',monospace; letter-spacing:.16em; text-transform:uppercase; }
.hero h1 { margin:6px 0 5px; font-size:36px; }
.hero p { color:var(--muted); margin:0; max-width:700px; }
.metric { background:linear-gradient(145deg,#101d31,#0c1422); border:1px solid var(--line); border-radius:14px; padding:17px 18px; min-height:105px; }
.metric .label { color:var(--muted); font:500 10px 'DM Mono',monospace; text-transform:uppercase; letter-spacing:.1em; }
.metric .value { font-size:30px; font-weight:700; margin-top:8px; }
.metric.cyan .value { color:var(--cyan); }.metric.red .value { color:var(--red); }.metric.orange .value { color:var(--orange); }.metric.blue .value { color:var(--blue); }
.section { color:var(--muted); font:500 11px 'DM Mono',monospace; letter-spacing:.12em; text-transform:uppercase; margin:26px 0 10px; }
.queue { border:1px solid var(--line); border-radius:14px; background:#0c1421; padding:16px; }
.queue.exception { border-left:3px solid var(--red); }.queue.review { border-left:3px solid var(--orange); }.queue.pass { border-left:3px solid var(--cyan); }
.queue-title { font-weight:700; font-size:16px; }.queue-sub { color:var(--muted); font-size:12px; margin-top:3px; }
.badge { display:inline-block; border-radius:99px; padding:4px 9px; font:500 10px 'DM Mono',monospace; letter-spacing:.04em; }
.badge.red { color:#ff9ab0; background:#5c1b31; }.badge.orange { color:#ffd18b; background:#5a3b17; }.badge.cyan { color:#94fff2; background:#124d4b; }
div[data-testid="stFileUploader"] { border:1px dashed #335178; border-radius:14px; padding:8px; background:#0b1422; }
.stButton>button { border:1px solid #2d4b73; border-radius:9px; background:#12223a; color:var(--text); transition:all .2s ease; }
.stButton>button:hover { border-color:var(--cyan); color:var(--cyan); box-shadow:0 0 20px #29e6d01c; }
button[kind="primary"] { background:linear-gradient(90deg,#087f82,#1479c9)!important; border:0!important; }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
[data-testid="stExpander"] { border:1px solid var(--line); border-radius:10px; background:#0c1421; }
code, .mono { font-family:'DM Mono',monospace; }
.small { color:var(--muted); font-size:12px; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def read_uploaded(uploaded) -> pd.DataFrame | None:
    try:
        return pd.read_csv(uploaded)
    except pd.errors.EmptyDataError:
        st.error("The CSV is empty.")
    except (pd.errors.ParserError, UnicodeDecodeError) as error:
        st.error(f"Could not read CSV: {error}")
    return None


def result_rows(results):
    rows = []
    for item in results:
        route = item.get("route", "UNKNOWN")
        rows.append({
            "Invoice ID": item.get("invoice_id"),
            "Queue": route,
            "Confidence": f"{item.get('confidence', 0):.0%}",
            "Rules": ", ".join(item.get("rule_ids", [])) or "—",
            "Explanation": item.get("explanation", ""),
        })
    return pd.DataFrame(rows)


def render_queue(title, subtitle, results, kind):
    st.markdown(
        f'<div class="queue {kind}"><div class="queue-title">{title} <span class="badge {kind}">{len(results):02d}</span></div><div class="queue-sub">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )
    if not results:
        st.caption("Queue clear — nothing here.")
        return
    st.dataframe(result_rows(results), use_container_width=True, hide_index=True)
    for item in results:
        label = f"{item.get('invoice_id') or 'NO ID'}  ·  {', '.join(item.get('rule_ids', [])) or 'No rule'}"
        with st.expander(label):
            st.write(item.get("explanation", "No explanation available."))
            details = item.get("rule_details", [])
            for reason in details:
                st.markdown(f"**{reason.get('rule')}** — {reason.get('message')}")
                st.caption(f"Actual: {reason.get('actual_value')}  |  Expected: {reason.get('expected_value')}")
            evidence = item.get("evidence_used")
            if evidence:
                st.json(evidence)


# ---------------------------------------------------------------------------
# Layout and input
# ---------------------------------------------------------------------------
st.sidebar.markdown("## ◈ FINSIGHT")
st.sidebar.caption("CONTROL CENTER / v2.0")
st.sidebar.divider()
st.sidebar.markdown("### CHECKING OPTIONS")
detailed = st.sidebar.toggle("Show detailed evidence", value=True)
show_raw = st.sidebar.toggle("Show uploaded rows", value=False)
st.sidebar.markdown("---")
st.sidebar.markdown("**QUEUE LEGEND**")
st.sidebar.markdown("🔴 **EXCEPTION** — deterministic rule failure")
st.sidebar.markdown("🟠 **HUMAN REVIEW** — ambiguous or incomplete")
st.sidebar.markdown("🟢 **AUTO-PASS** — all checks passed")

st.markdown(
    '<div class="hero"><div class="eyebrow">FINANCIAL CONTROL // LIVE CHECKER</div><h1>Invoice intelligence, without the noise.</h1><p>Upload a dataset, run deterministic checks, and send every invoice to the right queue — clearly separated into exceptions, human review, and auto-pass.</p></div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="section">01 / DATA INPUT</div>', unsafe_allow_html=True)
uploaded = st.file_uploader("Drop invoice CSV here", type="csv", label_visibility="collapsed")
if uploaded is None:
    st.info("Waiting for a CSV. Required columns: " + ", ".join(REQUIRED_COLUMNS))
    st.stop()

df = read_uploaded(uploaded)
if df is None:
    st.stop()
missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.stop()
if df.empty:
    st.warning("This file contains no invoice rows.")
    st.stop()
if show_raw:
    with st.expander(f"Raw input // {len(df)} rows"):
        st.dataframe(df, use_container_width=True, hide_index=True)

run = st.button("▶  RUN FULL CHECK", type="primary", use_container_width=True)
if run:
    try:
        st.session_state["results"] = process_invoice_dataframe(df)
        st.session_state["filename"] = uploaded.name
    except (TypeError, ValueError) as error:
        st.error(f"Validation could not run: {error}")
        st.stop()

results = st.session_state.get("results")
if not results:
    st.markdown('<div class="section">02 / READY STATE</div>', unsafe_allow_html=True)
    st.markdown('<div class="small">Run the full check to classify every invoice. The checker does not silently discard failed rows.</div>', unsafe_allow_html=True)
    st.stop()

passes = [x for x in results if x.get("route") == "AUTO_PASS"]
exceptions = [x for x in results if x.get("route") == "EXCEPTION"]
reviews = [x for x in results if x.get("route") == "HUMAN_REVIEW"]

st.markdown('<div class="section">03 / CHECK RESULT</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
for col, label, value, style in [(c1, "TOTAL SCANNED", len(results), "blue"), (c2, "AUTO-PASS", len(passes), "cyan"), (c3, "EXCEPTIONS", len(exceptions), "red"), (c4, "HUMAN REVIEW", len(reviews), "orange")]:
    col.markdown(f'<div class="metric {style}"><div class="label">{label}</div><div class="value">{value:02d}</div></div>', unsafe_allow_html=True)

st.caption(f"Source: {st.session_state.get('filename', uploaded.name)}  ·  {len(results)} records classified")

if detailed:
    st.markdown('<div class="section">04 / ROUTING QUEUES</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs([f"🔴 Exceptions ({len(exceptions)})", f"🟠 Human Review ({len(reviews)})", f"🟢 Auto-Pass ({len(passes)})"])
    with tab1:
        render_queue("Deterministic exceptions", "Clear rule failures that need correction before approval.", exceptions, "red")
    with tab2:
        render_queue("Human review queue", "Ambiguous, duplicate, or incomplete records requiring confirmation.", reviews, "orange")
    with tab3:
        render_queue("Approved automatically", "Invoices that passed every configured check.", passes, "cyan")
else:
    st.dataframe(result_rows(results), use_container_width=True, hide_index=True)

st.download_button("⇩ Download classified results", result_rows(results).to_csv(index=False), "finsight_classified_results.csv", "text/csv")
