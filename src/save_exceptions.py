from supabase_client import supabase

# Fetch invoices
response = supabase.table("invoices").select("*").execute()
invoices = response.data

MAX_AMOUNT = 10000

seen_ids = set()
exceptions = []

for invoice in invoices:
    invoice_id = invoice.get("invoice_id")
    vendor = invoice.get("vendor")
    amount = invoice.get("amount")

    reasons = []

    if invoice_id in seen_ids:
        reasons.append("Duplicate invoice ID")
    else:
        seen_ids.add(invoice_id)

    if not vendor:
        reasons.append("Missing vendor")

    if amount is None or amount <= 0:
        reasons.append("Invalid amount")

    if amount is not None and amount > MAX_AMOUNT:
        reasons.append("Amount exceeds limit")

    if reasons:
        exceptions.append({
            "invoice_id": invoice_id,
            "vendor": vendor,
            "amount": amount,
            "reasons": ", ".join(reasons)
        })

# Save exceptions
if exceptions:
    supabase.table("exceptions").insert(exceptions).execute()
    print("Exceptions saved successfully!")

print("Total exceptions:", len(exceptions))