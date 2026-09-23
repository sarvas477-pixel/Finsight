from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st

from src.audit_service import try_save_review, validate_review_action
from src.config import REQUIRED_COLUMNS
from src.invoice_pipeline import process_invoice_dataframe
from src.reporting import build_summary, filter_results, to_report_rows

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
:root { --bg:#070b14; --panel:#0d1422; --panel2:#111b2d; --line:#20304a; --text:#e7eefb; --muted:#8292ad; --cyan:#29e6d0; --blue:#5b8cff; --orange:#ffb454; --red:#ff6384; --green:#5be37a; }
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
.metric.cyan .value { color:var(--cyan); }.metric.red .value { color:var(--red); }.metric.orange .value { color:var(--orange); }.metric.blue .value { color:var(--blue); }.metric.green .value { color:var(--green); }
.section { color:var(--muted); font:500 11px 'DM Mono',monospace; letter-spacing:.12em; text-transform:uppercase; margin:26px 0 10px; }
.queue { border:1px solid var(--line); border-radius:14px; background:#0c1421; padding:16px; }
.queue.exception { border-left:3px solid var(--red); }.queue.review { border-left:3px solid var(--orange); }.queue.pass { border-left:3px solid var(--cyan); }
.queue-title { font-weight:700; font-size:16px; }.queue-sub { color:var(--muted); font-size:12px; margin-top:3px; }
.badge { display:inline-block; border-radius:99px; padding:4px 9px; font:500 10px 'DM Mono',monospace; letter-spacing:.04em; }
.badge.red { color:#ff9ab0; background:#5c1b31; }.badge.orange { color:#ffd18b; background:#5a3b17; }.badge.cyan { color:#94fff2; background:#124d4b; }.badge.green { color:#b6ffc4; background:#154a25; }
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


def audit_badge(item: dict) -> str:
    if item.get("audit_logged"):
        return '<span class="badge green">LOGGED</span>'
    return '<span class="badge orange">NOT LOGGED (no Supabase configured)</span>'


def render_review_controls(item: dict) -> None:
    """Approve/reject + comment box for the human-review queue (Day 12)."""
    invoice_id = item.get("invoice_id") or "UNKNOWN"
    state_key = f"review_status::{invoice_id}"
    comment_key = f"review_comment::{invoice_id}"

    existing = st.session_state.get(state_key)
    if existing:
        icon = "✅" if existing["action"] == "APPROVED" else "❌"
        st.success(f"{icon} {existing['action']} by {existing['reviewer_id']} — “{existing['comment']}”")
        if not existing.get("logged"):
            st.caption("Recorded locally for this session — not written to Supabase (no credentials configured).")
        return

    comment = st.text_area("Reviewer comment", key=comment_key, height=70)
    col_a, col_r = st.columns(2)
    approve = col_a.button("✅ Approve", key=f"approve::{invoice_id}", use_container_width=True)
    reject = col_r.button("❌ Reject", key=f"reject::{invoice_id}", use_container_width=True)

    action = "APPROVED" if approve else "REJECTED" if reject else None
    if action is None:
        return

    try:
        validate_review_action(action, comment)
    except ValueError as error:
        st.warning(str(error))
        return

    status = try_save_review(invoice_id, action, comment, reviewer_id="demo_reviewer")
    st.session_state[state_key] = {
        "action": action,
        "comment": comment.strip(),
        "reviewer_id": "demo_reviewer",
        "logged": status.get("success", False),
    }
    st.rerun()


def render_queue(title, subtitle, results, kind, show_review_controls=False):
    st.markdown(
        f'<div class="queue {kind}"><div class="queue-title">{title} <span class="badge {kind}">{len(results):02d}</span></div><div class="queue-sub">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )
    if not results:
        st.caption("Queue clear — nothing here.")
        return
    st.dataframe(pd.DataFrame(to_report_rows(results)), use_container_width=True, hide_index=True)
    for item in results:
        label = f"{item.get('invoice_id') or 'NO ID'}  ·  {', '.join(item.get('rule_ids', [])) or 'No rule'}"
        with st.expander(label):
            st.write(item.get("explanation", "No explanation available."))
            st.caption(f"Mode: {item.get('mode', '—')}")
            st.markdown(audit_badge(item), unsafe_allow_html=True)
            details = item.get("rule_details", [])
            for reason in details:
                st.markdown(f"**{reason.get('rule')}** — {reason.get('message')}")
                st.caption(f"Actual: {reason.get('actual_value')}  |  Expected: {reason.get('expected_value')}")
            evidence = item.get("evidence_used")
            if evidence:
                st.json(evidence)
            if show_review_controls:
                st.divider()
                render_review_controls(item)


# ---------------------------------------------------------------------------
# Layout and input
# ---------------------------------------------------------------------------
st.sidebar.markdown("## ◈ FINSIGHT")
st.sidebar.caption("CONTROL CENTER / v3.0")
st.sidebar.divider()
st.sidebar.markdown("### CHECKING OPTIONS")
detailed = st.sidebar.toggle("Show detailed evidence", value=True)
show_raw = st.sidebar.toggle("Show uploaded rows", value=False)
st.sidebar.markdown("---")
st.sidebar.markdown("**QUEUE LEGEND**")
st.sidebar.markdown("🔴 **EXCEPTION** — deterministic rule failure")
st.sidebar.markdown("🟠 **HUMAN REVIEW** — ambiguous or incomplete")
st.sidebar.markdown("🟢 **AUTO-PASS** — all checks passed")
st.sidebar.markdown("---")
st.sidebar.caption(
    "AI explanations use Gemini when GEMINI_API_KEY is set, and fall back to "
    "the deterministic template otherwise. Audit log and review actions use "
    "Supabase when SUPABASE_URL / SUPABASE_KEY are set."
)

st.markdown(
    '<div class="hero"><div class="eyebrow">FINANCIAL CONTROL // LIVE CHECKER</div><h1>Invoice intelligence, without the noise.</h1><p>Upload a dataset, run deterministic checks plus AI-explained review, and send every invoice to the right queue — with an audit trail on every decision.</p></div>',
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
        st.session_state["results"] = process_invoice_dataframe(df, filename=uploaded.name)
        st.session_state["filename"] = uploaded.name
        # Clear any stale review state from a previous file.
        for key in list(st.session_state.keys()):
            if key.startswith("review_status::"):
                del st.session_state[key]
    except (TypeError, ValueError) as error:
        st.error(f"Validation could not run: {error}")
        st.stop()

results = st.session_state.get("results")
if not results:
    st.markdown('<div class="section">02 / READY STATE</div>', unsafe_allow_html=True)
    st.markdown('<div class="small">Run the full check to classify every invoice. The checker does not silently discard failed rows.</div>', unsafe_allow_html=True)
    st.stop()

summary = build_summary(results)

st.markdown('<div class="section">03 / CHECK RESULT</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
for col, label, value, style in [
    (c1, "TOTAL SCANNED", summary["total"], "blue"),
    (c2, "AUTO-PASS", summary["auto_pass"], "cyan"),
    (c3, "EXCEPTIONS", summary["exceptions"], "red"),
    (c4, "HUMAN REVIEW", summary["human_review"], "orange"),
    (c5, "AUDIT LOGGED", summary["audit_logged"], "green"),
]:
    col.markdown(f'<div class="metric {style}"><div class="label">{label}</div><div class="value">{value:02d}</div></div>', unsafe_allow_html=True)

st.caption(f"Source: {st.session_state.get('filename', uploaded.name)}  ·  {len(results)} records classified")

# ---------------------------------------------------------------------------
# Filters (Day 13)
# ---------------------------------------------------------------------------
st.markdown('<div class="section">04 / SEARCH & FILTER</div>', unsafe_allow_html=True)
f1, f2 = st.columns([3, 1])
search_query = f1.text_input("Search by invoice ID, rule, or explanation text", value="", label_visibility="collapsed", placeholder="Search invoice ID, rule ID, or explanation text…")
route_filter = f2.selectbox("Queue", ["ALL", "EXCEPTION", "HUMAN_REVIEW", "AUTO_PASS"], label_visibility="collapsed")

visible_results = filter_results(results, query=search_query, route=route_filter)
if search_query or route_filter != "ALL":
    st.caption(f"Showing {len(visible_results)} of {len(results)} records matching filters.")

passes = [x for x in visible_results if x.get("route") == "AUTO_PASS"]
exceptions = [x for x in visible_results if x.get("route") == "EXCEPTION"]
reviews = [x for x in visible_results if x.get("route") == "HUMAN_REVIEW"]

if detailed:
    st.markdown('<div class="section">05 / ROUTING QUEUES</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs([f"🔴 Exceptions ({len(exceptions)})", f"🟠 Human Review ({len(reviews)})", f"🟢 Auto-Pass ({len(passes)})"])
    with tab1:
        render_queue("Deterministic exceptions", "Clear rule failures that need correction before approval.", exceptions, "red")
    with tab2:
        render_queue("Human review queue", "Ambiguous, duplicate, or incomplete records requiring confirmation.", reviews, "orange", show_review_controls=True)
    with tab3:
        render_queue("Approved automatically", "Invoices that passed every configured check.", passes, "cyan")
else:
    st.dataframe(pd.DataFrame(to_report_rows(visible_results)), use_container_width=True, hide_index=True)

st.markdown('<div class="section">06 / EXPORT</div>', unsafe_allow_html=True)
st.download_button(
    "⇩ Download classified results",
    pd.DataFrame(to_report_rows(visible_results)).to_csv(index=False),
    "finsight_classified_results.csv",
    "text/csv",
)
