import pandas as pd

from src.rule_engine import process_invoices
from src.explanation import create_prompt


# Read invoice data
df = pd.read_csv("data/invoices.csv")

# M1 processes the invoices
results = process_invoices(df)

# M2 creates prompts from M1's results
for result in results:

    if result["status"] == "EXCEPTION":

        prompt = create_prompt(result)

        print("\n" + "=" * 50)
        print(prompt)