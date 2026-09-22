"""Single invoice-processing pipeline used by the UI and CLI."""
from __future__ import annotations

from typing import Any

import pandas as pd

from src.day6_structured_explanation import create_structured_explanation
from src.day7_routing import add_confidence_and_routing
from src.rule_engine import process_invoices


def process_invoice_dataframe(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Validate, process, explain, and route every invoice consistently."""
    return [
        add_confidence_and_routing(create_structured_explanation(result))
        for result in process_invoices(df)
    ]


def process_invoice_csv(path: str) -> list[dict[str, Any]]:
    """Read and process an invoice CSV through the shared pipeline."""
    from src.paths import resolve_csv

    return process_invoice_dataframe(pd.read_csv(resolve_csv(path)))
