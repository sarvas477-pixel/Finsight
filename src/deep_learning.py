"""Deep-learning anomaly detection for FinSight invoices.

This module is deliberately independent from the deterministic rule engine.
It uses a small neural autoencoder (scikit-learn MLPRegressor) to learn the
shape of normal invoice records and return a 0..1 anomaly score.

The detector is advisory: it never replaces policy rules or human review.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

FEATURES = (
    "log_amount",
    "amount_limit_ratio",
    "category_code",
    "vendor_frequency",
    "day_of_month",
    "day_of_week",
    "month",
)

MIN_TRAIN_ROWS = 8
MIN_VARIANCE = 1e-9
ANOMALY_PERCENTILE = 95.0


@dataclass
class DeepLearningResult:
    available: bool
    score: float
    status: str
    reason: str
    reconstruction_error: float = 0.0


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        value = float(value)
        return value if np.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def _category_code(value: Any, categories: list[str]) -> float:
    text = "" if pd.isna(value) else str(value).strip().casefold()
    if text in categories:
        return float(categories.index(text) + 1)
    return 0.0


def build_features(df: pd.DataFrame, category_limits: dict[str, float]) -> pd.DataFrame:
    """Convert invoice rows into stable numerical features for the autoencoder."""
    work = df.copy()
    amounts = pd.to_numeric(work.get("amount"), errors="coerce").fillna(0.0).clip(lower=0.0)
    categories = [str(k).strip().casefold() for k in category_limits]
    category_lookup = {
        str(k).strip().casefold(): float(v) for k, v in category_limits.items()
    }

    cat_norm = work.get("category", pd.Series(index=work.index, dtype="object")).fillna("").astype(str).str.strip().str.casefold()
    limits = cat_norm.map(category_lookup).fillna(0.0)
    ratios = np.where(limits.to_numpy() > 0, amounts.to_numpy() / limits.to_numpy(), amounts.to_numpy() / max(max(category_lookup.values(), default=1.0), 1.0))

    dates = pd.to_datetime(
        work.get("invoice_date", pd.Series(index=work.index, dtype="object")),
        errors="coerce",
    )
    vendors = work.get("vendor", pd.Series(index=work.index, dtype="object")).fillna("").astype(str).str.strip().str.casefold()
    frequencies = vendors.map(vendors.value_counts()).fillna(0).astype(float)

    features = pd.DataFrame(index=work.index)
    features["log_amount"] = np.log1p(amounts)
    features["amount_limit_ratio"] = np.clip(ratios, 0.0, 20.0)
    features["category_code"] = cat_norm.map(lambda x: _category_code(x, categories)).astype(float)
    features["vendor_frequency"] = np.log1p(frequencies)
    features["day_of_month"] = dates.dt.day.fillna(0).astype(float)
    features["day_of_week"] = dates.dt.dayofweek.fillna(-1).astype(float) + 1.0
    features["month"] = dates.dt.month.fillna(0).astype(float)
    return features[list(FEATURES)].replace([np.inf, -np.inf], 0.0).fillna(0.0)


def _make_training_frame(features: pd.DataFrame) -> pd.DataFrame | None:
    """Build a modest normal-only training set from the current batch.

    Real clean invoices are preferred. If the batch is small, deterministic
    jittered copies provide enough numerical diversity to fit the autoencoder.
    """
    if len(features) == 0:
        return None

    base = features.copy()
    if len(base) >= MIN_TRAIN_ROWS:
        return base

    rng = np.random.default_rng(42)
    copies = [base]
    scale = base.std(ddof=0).replace(0, 1.0).to_numpy()
    for multiplier in range(1, 4):
        noise = rng.normal(0.0, 0.025 * multiplier, size=base.shape)
        jittered = base.to_numpy() + noise * scale
        copies.append(pd.DataFrame(jittered, columns=base.columns))
    expanded = pd.concat(copies, ignore_index=True)
    return expanded if len(expanded) >= MIN_TRAIN_ROWS else None


def score_invoices(
    df: pd.DataFrame,
    category_limits: dict[str, float],
    normal_mask: pd.Series | None = None,
) -> list[DeepLearningResult]:
    """Train an invoice autoencoder and score each row.

    The model is intentionally fitted per analysis batch to avoid persisting
    untrusted invoice data. For production, this can be replaced by a model
    trained on historical approved invoices.
    """
    features = build_features(df, category_limits)
    if len(features) < 2:
        return [
            DeepLearningResult(False, 0.0, "UNAVAILABLE", "Not enough invoice rows.")
            for _ in range(len(df))
        ]

    training = features
    if normal_mask is not None:
        mask = pd.Series(normal_mask, index=df.index).fillna(False).astype(bool)
        clean_features = features.loc[mask]
        if len(clean_features) >= MIN_TRAIN_ROWS:
            training = clean_features

    training = _make_training_frame(training)
    if training is None or len(training) < MIN_TRAIN_ROWS:
        return [
            DeepLearningResult(False, 0.0, "UNAVAILABLE", "Not enough training data.")
            for _ in range(len(df))
        ]

    scaler = StandardScaler()
    x_train = scaler.fit_transform(training)
    x_all = scaler.transform(features)

    hidden = max(4, min(16, len(FEATURES) * 2))
    model = MLPRegressor(
        hidden_layer_sizes=(hidden, 8),
        activation="relu",
        solver="lbfgs",
        alpha=1e-3,
        max_iter=500,
        random_state=42,
    )
    try:
        model.fit(x_train, x_train)
        reconstructed = model.predict(x_all)
    except Exception as exc:
        return [
            DeepLearningResult(False, 0.0, "UNAVAILABLE", f"Model training failed: {exc}")
            for _ in range(len(df))
        ]

    errors = np.mean(np.square(x_all - reconstructed), axis=1)
    train_reconstructed = model.predict(x_train)
    train_errors = np.mean(np.square(x_train - train_reconstructed), axis=1)
    baseline = float(np.percentile(train_errors, ANOMALY_PERCENTILE))
    spread = float(np.std(train_errors))
    scale_error = max(baseline + 2.0 * spread, MIN_VARIANCE)

    # Score is continuous and bounded. 0.5 roughly means the row is around
    # the learned normal envelope; values near 1 are increasingly unusual.
    scores = 1.0 - np.exp(-np.maximum(errors - baseline, 0.0) / scale_error)
    threshold = 0.65

    output = []
    for error, score in zip(errors, scores):
        score = float(np.clip(score, 0.0, 1.0))
        status = "ANOMALY" if score >= threshold else "NORMAL"
        reason = (
            "Neural autoencoder found an unusual invoice pattern."
            if status == "ANOMALY"
            else "Invoice pattern is within the learned normal range."
        )
        output.append(
            DeepLearningResult(
                True,
                score,
                status,
                reason,
                float(error),
            )
        )
    return output
