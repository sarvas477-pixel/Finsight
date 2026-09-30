"""Train FinSight's supervised AI risk model.

Usage:
  python scripts/train_ai.py data/training_invoices.csv
The CSV should contain the normal invoice columns and optionally risk_label (0/1).
If risk_label is absent, weak labels are generated from the existing rule policy.
"""
from __future__ import annotations

import sys
import pandas as pd
from src.config import CATEGORY_LIMITS
from src.trained_ai import train_model

source = sys.argv[1] if len(sys.argv) > 1 else "data/training_invoices.csv"
df = pd.read_csv(source)
meta = train_model(df, CATEGORY_LIMITS)
print("FinSight AI model trained")
print(meta)
