# FinSight — AI Accounts-Payable Exception Assistant

FinSight checks invoice CSVs with a deterministic rule engine, explains every decision with evidence, routes uncertain cases to human review, and provides an evidence-grounded AI chat assistant.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app/app.py
```

Add `GEMINI_API_KEY` to `.env` for the real Gemini assistant. Without it, FinSight uses a deterministic fallback so the product still works.

## CSV format

Required columns:
`invoice_id,vendor,amount,category,invoice_date`

Configured category limits are in `src/config.py`.

## Product rules

- The deterministic rule engine is the source of truth.
- Gemini explains trusted evidence and never changes the decision.
- AI answers are restricted to the current analyzed invoice dataset.
- Possible duplicates and other uncertain cases can be routed to human review.
- Review actions and audit events are kept in the current session and can optionally be persisted to Supabase.
