# FinSight — AI Accounts-Payable Exception Assistant

FinSight is an evidence-first invoice/AP workspace. The Python rule engine is the source of truth; the AI Copilot explains trusted results but never changes invoice decisions.

## Included in this release

- Required-field, amount, date, category-limit and duplicate validation
- CLEAN / EXCEPTION status plus AUTO_PASS / HUMAN_REVIEW routing
- Confidence, rule IDs, evidence and matched-record context
- Dark Cybernetic Audit Control Streamlit frontend
- CSV upload plus bundled sample dataset
- Queue filters: All / Auto-pass / Exceptions / Human review
- Literal, case-insensitive result search
- Reviewer approve/reject actions with comments
- Evidence inspector for each invoice
- CSV exports for analyzed results, exceptions and original data
- Session audit trail and batched Supabase audit persistence
- Persisted audit-log viewer
- FinSight Copilot with deterministic answers first and optional Gemini grounding
- Scope guard for unrelated questions
- Live Gemini and Supabase connection checks
- Automated rule-engine, reporting, persistence and frontend smoke tests
- Streamlit Community Cloud entrypoint

## Local run

~~~powershell
py -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\\.venv\\Scripts\\python.exe -m pytest -q
.\\.venv\\Scripts\\python.exe -m streamlit run streamlit_app.py
~~~

Activation is optional on Windows; invoking the venv Python directly also works.

## Environment

~~~env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.6-flash
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_key
~~~

Never commit real credentials. supabase_schema.sql contains the audit table definition.

## Architecture

CSV -> deterministic Python rule engine -> evidence/routing -> human review + audit persistence -> Copilot explanation

Gemini is optional. If it is unavailable, deterministic FinSight responses and invoice analysis continue to work.
