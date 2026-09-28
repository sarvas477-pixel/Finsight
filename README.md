# FinSight — AI Accounts-Payable Exception Assistant

FinSight is a modern AP operations workspace that combines deterministic invoice controls, evidence, human review, and an evidence-grounded AI copilot.

## What is implemented

- Required-field, amount, date, category-limit and duplicate validation
- Deterministic `AUTO_PASS`, `EXCEPTION`, and `HUMAN_REVIEW` routing
- Evidence and confidence metadata for every result
- Modern Streamlit command center with responsive cards, hover motion, animated transitions, accessible focus states, and a chatbot-first AI Copilot
- Reviewer approve/reject workflow with comments
- Session audit trail and optional Supabase persistence
- Gemini-powered natural-language explanations grounded only in trusted rule-engine results
- CSV results and JSON audit exports
- Automated tests
- Streamlit Community Cloud entrypoint: `streamlit_app.py`

## Run locally on Windows

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

If PowerShell blocks activation, activation is not required.

## Gemini connection

FinSight reads these values from either environment variables or Streamlit Secrets:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

The AI Copilot uses deterministic answers for common AP questions first. For broader questions, Gemini receives only the trusted invoice-analysis payload. Gemini never becomes the source of truth for invoice decisions.

The sidebar's **Check connections** action performs a live Gemini test.

## Supabase connection

Create the `audit_events` table with:

```text
supabase_schema.sql
```

Configure:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_key
```

FinSight uses Supabase for best-effort audit persistence. The local/session workflow remains usable if Supabase is unavailable.

The sidebar's **Check connections** action tests access to the `audit_events` table.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud and create an app.
3. Select repository `sarvas477-pixel/Finsight`.
4. Set the branch to `main`.
5. Set the main file to `streamlit_app.py`.
6. Open **Advanced settings → Secrets**.
7. Paste:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
GEMINI_MODEL = "gemini-2.5-flash"

SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your_supabase_key"
```

8. Deploy, open the app, load the sample CSV, click **Analyze**, then use **AI Copilot**.
9. Open the sidebar and click **Check connections** to verify Gemini and Supabase.

Do **not** commit `.env` or `.streamlit/secrets.toml` to GitHub.

## CSV format

```csv
invoice_id,vendor,amount,category,invoice_date
```

Configured limits live in `src/config.py`.

## Architecture

```
CSV
 ↓
Deterministic Rule Engine
 ↓
Trusted Evidence + Route
 ├── AUTO_PASS
 ├── EXCEPTION
 └── HUMAN_REVIEW
          ↓
     FinSight Copilot
          ↓
   Gemini (optional)
          ↓
     Audit / Export
```

The deterministic rule engine remains the source of truth. The LLM explains trusted results rather than silently changing them.

## Release gate

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

See `docs.md` and `DAY20_COMPLETION.md` for the project and demo checklist.
