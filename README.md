# FinSight (AuditMate AI)

FinSight is an accounts-payable exception assistant: upload an invoice CSV,
and every row is checked, explained, routed, and logged automatically.

The deterministic rule engine is always the source of truth. AI only adds or
validates explanations and never changes a decision or route.

## Run it

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m pytest -q
python -m src.main tests/fixtures/fake_invoices.csv
streamlit run app/app.py
```

Required invoice columns: `invoice_id`, `vendor`, `amount`, `category`, and
`invoice_date`.

## Pipeline

```text
CSV
  -> deterministic rule engine
  -> structured explanation
  -> confidence and routing
  -> evidence-only AI explanation or template fallback
  -> quality guard
  -> audit logging
```

The dashboard provides Exceptions, Human Review, and Auto-Pass queues; search,
filters, evidence, review controls, and CSV export. Gemini and Supabase are
optional. Without credentials, explanations and audit/review behavior fall
back safely to offline mode.

## Supabase tables

- `audit_events` — one row per invoice decision
- `review_actions` — one row per human review action

## Chatbot

The grounded read-only assistant uses only current deterministic processing
results. It supports invoice, rule, duplicate, summary, and queue questions.
Set `GEMINI_API_KEY` to enable Gemini; otherwise it uses deterministic answers.
It rejects unsupported citations and never approves, rejects, or changes an
invoice.
