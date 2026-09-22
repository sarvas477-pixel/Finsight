"""Command-line entry point for the deterministic invoice checker."""
from __future__ import annotations

import argparse
import json

import pandas as pd

from src.invoice_pipeline import process_invoice_dataframe
from src.paths import resolve_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a FinSight invoice CSV")
    parser.add_argument("csv", nargs="?", help="CSV path; defaults to data/invoices.csv")
    args = parser.parse_args()

    df = pd.read_csv(resolve_csv(args.csv))
    results = process_invoice_dataframe(df)
    print(json.dumps(results, indent=2, allow_nan=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
