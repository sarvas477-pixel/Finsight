# FinSight

FinSight is an invoice exception checker with a browser-based finance workspace and a deterministic Python invoice pipeline.

## Run the invoice checker

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m pytest -q
python -m src.main tests/fixtures/fake_invoices.csv
streamlit run app/app.py
```

The invoice pipeline does not require Supabase credentials. Supabase is optional and is initialized lazily only by code that accesses `src.supabase_client.supabase`.

Required invoice columns are `invoice_id`, `vendor`, `amount`, `category`, and `invoice_date`.
