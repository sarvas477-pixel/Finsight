import pandas as pd
from pathlib import Path


data = {
    "invoice_id": ["INV001", "INV002", "INV003", "INV004", "INV005"],
    "vendor": [
        "ABC Suppliers",
        "XYZ Technologies",
        "ABC Suppliers",
        "Office Mart",
        "",
    ],
    "amount": [4500, 15000, 4500, 800, 1200],
    "category": ["Travel", "Equipment", "Travel", "Office", "Travel"],
    "invoice_date": [
        "2026-09-14",
        "2026-09-14",
        "2026-09-14",
        "2026-09-14",
        "2026-09-14",
    ],
}

df = pd.DataFrame(data)

Path("data").mkdir(exist_ok=True)

df.to_csv("data/invoices.csv", index=False)

print("Invoice dataset created successfully!")
print(df.to_string(index=False))