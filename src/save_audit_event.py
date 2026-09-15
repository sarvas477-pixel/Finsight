from supabase_client import supabase

audit_record = {
    "event_type": "TEST",
    "invoice_id": "INV001",
    "message": "Test audit event created successfully"
}

response = supabase.table("audit_events").insert(audit_record).execute()

print("Audit event saved successfully!")
print(response.data)