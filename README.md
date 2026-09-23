# FinSight (AuditMate AI)

FinSight is an accounts-payable exception assistant: upload an invoice CSV,
and every row is checked, explained, routed, and logged automatically.

**Pipeline (all wired together in `src/invoice_pipeline.py`):**

```
CSV
  -> rule engine (required fields, category limits, duplicates)      src/rule_engine.py
  -> structured explanation                                          src/day6_structured_explanation.py
  -> confidence + routing (AUTO_PASS / EXCEPTION / HUMAN_REVIEW)     src/day7_routing.py
  -> evidence-only AI explanation (Gemini, or template fallback)     src/day8_evidence_prompt.py, src/day9_ai_explainer.py
  -> quality guard (rejects unsupported AI claims)                   src/quality_guard.py
  -> audit log every decision                                        src/audit_logger.py, src/audit_service.py
```

The deterministic rule engine is always the source of truth — the AI step
only adds or validates an explanation, and never changes a decision or route.

## Run it

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional: copy .env.example -> .env and fill in GEMINI_API_KEY / SUPABASE_URL / SUPABASE_KEY.
# Everything below works with none of these set — it just runs in
template-fallback / not-logged mode instead of AI / Supabase mode.

python -m pytest -q
python -m src.main tests/fixtures/fake_invoices.csv
streamlit run app/app.py
```

Required invoice columns: `invoice_id`, `vendor`, `amount`, `category`, `invoice_date`.

## What's in the dashboard

- Upload a CSV, run the check, and every row lands in one of three queues:
  Exceptions, Human Review, Auto-Pass.
- Search/filter by invoice ID, rule ID, or explanation text, and filter by queue.
- Each flagged row shows its evidence, matched rule(s), which mode explained it
  (`deterministic` / `ai_response` / `template_fallback` / `quality_guard_fallback`),
  and whether it was written to the audit log.
- Human Review rows have Approve/Reject buttons with a required reviewer comment.
  These are recorded to Supabase's `review_actions` table when configured, and
  shown inline for the session either way.
- Download the classified results (respecting your active filters) as CSV.

## Supabase tables expected

- `audit_events` — one row per invoice decision (see `src/audit_logger.py` for the shape)
- `review_actions` — one row per human review action (see `src/save_review.py`)

## Tests

`tests/` covers the rule engine, routing, evidence verification, human-review
validation, and the reporting/filter helpers. None of the tests require
Supabase or Gemini credentials — invalid input is rejected before any
external call is made, and pipeline runs work fully offline.
