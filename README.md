# FinSight — AI Accounts-Payable Exception Assistant

FinSight is a submission-ready prototype for the Accounts-Payable Exception Assistant problem. It validates invoice CSVs with a deterministic rule engine, preserves evidence, routes uncertain cases to human review, provides an evidence-grounded AI assistant, and exports audit/results data.

## What is implemented
- Required-field validation
- Amount/date validation
- Configurable category spending limits
- Duplicate invoice-ID detection
- Possible duplicate-record detection with matched invoice IDs
- Deterministic `AUTO_PASS`, `EXCEPTION`, and `HUMAN_REVIEW` routing
- Confidence metadata that never overrides deterministic decisions
- Evidence for every flag
- FinSight AI chat with deterministic intent handling + Gemini fallback/LLM mode
- Reviewer approve/reject actions and comments
- Session audit log and optional Supabase persistence
- CSV result and JSON audit exports
- Automated tests and malformed-input handling
- No login required

## Run locally on Windows
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app/app.py
```

If PowerShell blocks activation, you do not need activation: use the `.venv\Scripts\python.exe` commands above.

## AI assistant
Put the live key only in `.env`:
```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```
Without a key, deterministic assistant handlers and a safe template fallback keep the product usable.

This is not a fine-tuned foundation model. The assistant is deliberately grounded at runtime using FinSight's domain knowledge plus the current trusted rule-engine results. This is safer for an AP prototype because the LLM cannot silently override a deterministic invoice decision.

## CSV format
```csv
invoice_id,vendor,amount,category,invoice_date
```
Configured limits live in `src/config.py`.

## Optional Supabase
Set `SUPABASE_URL` and `SUPABASE_KEY` in `.env` and create the table using `supabase_schema.sql`. The app remains functional when Supabase is unavailable.

## Release gate
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

See `docs.md` for the Day 16–20 completion and demo checklist.