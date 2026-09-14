from supabase_client import supabase

# Fetch all invoices
response = supabase.table("invoices").select("*").execute()

invoices = response.data

print("Total invoices:", len(invoices))

for invoice in invoices:
    print(invoice)