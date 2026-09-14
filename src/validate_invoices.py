from supabase_client import supabase

# Fetch invoices
response = supabase.table("invoices").select("*").execute()
invoices = response.data

# Spending limit
MAX_AMOUNT = 10000

seen_ids = set()
exceptions = []

for invoice in invoices:
    invoice_id = invoice.get("invoice_id")
    vendor = invoice.get("vendor")
    amount = invoice.get("amount")

    reasons = []

    # Check duplicate invoice ID
    if invoice_id in seen_ids:
        reasons.append("Duplicate invoice ID")
    else:
        seen_ids.add(invoice_id)

    # Check vendor
    if not vendor:
        reasons.append("Missing vendor")

    # Check amount
    if amount is None or amount <= 0:
        reasons.append("Invalid amount")

    # Check spending limit
    if amount is not None and amount > MAX_AMOUNT:
        reasons.append("Amount exceeds limit")

    # Store exception
    if reasons:
        exceptions.append({
            "invoice_id": invoice_id,
            "vendor": vendor,
            "amount": amount,
            "reasons": ", ".join(reasons)
        })

# Display results
print("Total invoices:", len(invoices))
print("Total exceptions:", len(exceptions))

for exception in exceptions:
    print(exception)