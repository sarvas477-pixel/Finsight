import pandas as pd
from supabase_client import supabase

# Read CSV
df = pd.read_csv("data/invoices.csv")

# Rename CSV column to match Supabase
df = df.rename(columns={
    "date": "invoice_date"
})

# Convert missing values to None
records = df.where(pd.notnull(df), None).to_dict(orient="records")

# Upload to Supabase
response = supabase.table("invoices").insert(records).execute()

print("Invoices uploaded successfully!")
print(response.data)