"""FinSight deep-learning anomaly detector.

Uses a small PyTorch autoencoder to learn the normal numeric/structural
pattern of the currently analyzed invoice batch. It never replaces the
deterministic rule engine; it adds an independent anomaly signal.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn


MIN_ROWS = 12
ANOMALY_THRESHOLD = 0.85
EPOCHS = 80


class InvoiceAutoencoder(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        hidden = max(8, min(32, input_dim * 2))
        bottleneck = max(4, min(16, input_dim))
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, bottleneck),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(bottleneck, hidden),
            nn.ReLU(),
            nn.Linear(hidden, input_dim),
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


def _features(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)

    amount = pd.to_numeric(df.get("amount"), errors="coerce").fillna(0).clip(lower=0)
    out["log_amount"] = np.log1p(amount)

    dates = pd.to_datetime(df.get("invoice_date"), errors="coerce")
    out["year"] = dates.dt.year.fillna(0).astype(float)
    out["month"] = dates.dt.month.fillna(0).astype(float)
    out["day"] = dates.dt.day.fillna(0).astype(float)
    out["weekday"] = dates.dt.dayofweek.fillna(0).astype(float)

    category = df.get("category", pd.Series("", index=df.index)).fillna("").astype(str).str.casefold()
    for value in ("office", "it", "travel", "food", "equipment", "other"):
        out[f"cat_{value}"] = category.eq(value).astype(float)

    vendor = df.get("vendor", pd.Series("", index=df.index)).fillna("").astype(str).str.casefold()
    vendor_counts = vendor.value_counts()
    out["vendor_frequency"] = vendor.map(vendor_counts).fillna(0).astype(float)

    return out.replace([np.inf, -np.inf], 0).fillna(0)


def _scale(frame: pd.DataFrame):
    values = frame.to_numpy(dtype=np.float32)
    mean = values.mean(axis=0)
    std = values.std(axis=0)
    std[std < 1e-6] = 1.0
    return (values - mean) / std


def analyze_with_deep_learning(df: pd.DataFrame) -> dict[str, Any]:
    """Train an autoencoder on the batch and return one anomaly score per row."""
    n = len(df)
    if n < MIN_ROWS:
        return {
            "available": False,
            "reason": f"Deep learning needs at least {MIN_ROWS} invoices.",
            "scores": [None] * n,
            "flags": [False] * n,
            "model": "PyTorch Invoice Autoencoder",
            "epochs": 0,
        }

    try:
        torch.manual_seed(42)
        np.random.seed(42)
        frame = _features(df)
        scaled = _scale(frame)
        x = torch.tensor(scaled, dtype=torch.float32)

        model = InvoiceAutoencoder(x.shape[1])
        optimizer = torch.optim.Adam(model.parameters(), lr=0.008, weight_decay=1e-5)
        loss_fn = nn.MSELoss()
        model.train()

        for _ in range(EPOCHS):
            optimizer.zero_grad()
            reconstructed = model(x)
            loss = loss_fn(reconstructed, x)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            reconstructed = model(x)
            errors = ((reconstructed - x) ** 2).mean(dim=1).numpy()

        low, high = float(errors.min()), float(errors.max())
        if math.isclose(low, high):
            scores = np.zeros(n, dtype=float)
        else:
            # Robust percentile-like normalization: the largest reconstruction
            # error maps to 1.0 and the rest remain comparable within the batch.
            scores = np.clip((errors - low) / (high - low), 0, 1)

        flags = scores >= ANOMALY_THRESHOLD

        return {
            "available": True,
            "reason": "Deep-learning anomaly detection completed.",
            "scores": [round(float(x), 4) for x in scores],
            "flags": [bool(x) for x in flags],
            "model": "PyTorch Invoice Autoencoder",
            "epochs": EPOCHS,
            "anomalies": int(flags.sum()),
        }
    except Exception as exc:
        return {
            "available": False,
            "reason": f"Deep learning unavailable: {exc}",
            "scores": [None] * n,
            "flags": [False] * n,
            "model": "PyTorch Invoice Autoencoder",
            "epochs": 0,
        }
