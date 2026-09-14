
import pandas as pd
from pathlib import Path

# Create fake invoice data
data = {
    "invoice_id": ["INV001", "INV002", "INV003", "INV004", "INV005"],
    "vendor": ["ABC Supplies", "Tech World", "ABC Supplies", "Office Mart", "Tech World"],
    "amount": [5000, 15000, 5000, 2500, 12000],
    "category": ["Office", "IT", "Office", "Office", "IT"],
    "date": [
        "2026-09-01",
        "2026-09-02",
        "2026-09-03",
        "2026-09-04",
        "2026-09-05"
    ]
}

# Convert data into a DataFrame
df = pd.DataFrame(data)

# Create data folder if it does not exist
Path("data").mkdir(exist_ok=True)

# Save the data as a CSV file
df.to_csv("data/invoices.csv", index=False)

# Display the dataset
print("Invoice dataset created successfully!")
print(df)