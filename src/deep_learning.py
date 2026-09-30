"""Deep-learning anomaly detection for FinSight invoices."""
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


def _category_code(value: Any, categories: list[str]) -> float:
    text = "" if pd.isna(value) else str(value).strip().casefold()
    return float(categories.index(text) + 1) if text in categories else 0.0


def build_features(df: pd.DataFrame, category_limits: dict[str, float]) -> pd.DataFrame:
    work = df.copy()
    amounts = pd.to_numeric(work.get("amount"), errors="coerce").fillna(0.0).clip(lower=0.0)
    categories = [str(k).strip().casefold() for k in category_limits]
    lookup = {str(k).strip().casefold(): float(v) for k, v in category_limits.items()}
    cat = work.get("category", pd.Series(index=work.index, dtype="object")).fillna("").astype(str).str.strip().str.casefold()
    limits = cat.map(lookup).fillna(0.0)
    fallback = max(max(lookup.values(), default=1.0), 1.0)
    ratios = np.where(limits.to_numpy() > 0, amounts.to_numpy() / limits.to_numpy(), amounts.to_numpy() / fallback)
    dates = pd.to_datetime(work.get("invoice_date", pd.Series(index=work.index, dtype="object")), errors="coerce")
    vendors = work.get("vendor", pd.Series(index=work.index, dtype="object")).fillna("").astype(str).str.strip().str.casefold()
    frequency = vendors.map(vendors.value_counts()).fillna(0).astype(float)

    features = pd.DataFrame(index=work.index)
    features["log_amount"] = np.log1p(amounts)
    features["amount_limit_ratio"] = np.clip(ratios, 0.0, 20.0)
    features["category_code"] = cat.map(lambda x: _category_code(x, categories))
    features["vendor_frequency"] = np.log1p(frequency)
    features["day_of_month"] = dates.dt.day.fillna(0).astype(float)
    features["day_of_week"] = dates.dt.dayofweek.fillna(-1).astype(float) + 1.0
    features["month"] = dates.dt.month.fillna(0).astype(float)
    return features[list(FEATURES)].replace([np.inf, -np.inf], 0.0).fillna(0.0)


def _training_frame(features: pd.DataFrame) -> pd.DataFrame | None:
    if len(features) == 0:
        return None
    if len(features) >= MIN_TRAIN_ROWS:
        return features
    rng = np.random.default_rng(42)
    scale = features.std(ddof=0).replace(0, 1.0).to_numpy()
    frames = [features]
    for multiplier in range(1, 4):
        noise = rng.normal(0.0, 0.025 * multiplier, size=features.shape)
        frames.append(pd.DataFrame(features.to_numpy() + noise * scale, columns=features.columns))
    expanded = pd.concat(frames, ignore_index=True)
    return expanded if len(expanded) >= MIN_TRAIN_ROWS else None


def score_invoices(df: pd.DataFrame, category_limits: dict[str, float], normal_mask: pd.Series | None = None) -> list[DeepLearningResult]:
    features = build_features(df, category_limits)
    if len(features) < 2:
        return [DeepLearningResult(False, 0.0, "UNAVAILABLE", "Not enough invoice rows.") for _ in range(len(df))]

    training = features
    if normal_mask is not None:
        mask = pd.Series(normal_mask, index=df.index).fillna(False).astype(bool)
        clean = features.loc[mask]
        if len(clean) >= MIN_TRAIN_ROWS:
            training = clean

    training = _training_frame(training)
    if training is None:
        return [DeepLearningResult(False, 0.0, "UNAVAILABLE", "Not enough training data.") for _ in range(len(df))]

    try:
        scaler = StandardScaler()
        x_train = scaler.fit_transform(training)
        x_all = scaler.transform(features)
        model = MLPRegressor(
            hidden_layer_sizes=(max(4, min(16, len(FEATURES) * 2)), 8),
            activation="relu", solver="lbfgs", alpha=1e-3, max_iter=500, random_state=42,
        )
        model.fit(x_train, x_train)
        reconstructed = model.predict(x_all)
        train_reconstructed = model.predict(x_train)
    except Exception as exc:
        return [DeepLearningResult(False, 0.0, "UNAVAILABLE", f"Model training failed: {exc}") for _ in range(len(df))]

    errors = np.mean(np.square(x_all - reconstructed), axis=1)
    train_errors = np.mean(np.square(x_train - train_reconstructed), axis=1)
    baseline = float(np.percentile(train_errors, ANOMALY_PERCENTILE))
    spread = float(np.std(train_errors))
    scale_error = max(baseline + 2.0 * spread, MIN_VARIANCE)
    scores = 1.0 - np.exp(-np.maximum(errors - baseline, 0.0) / scale_error)

    output: list[DeepLearningResult] = []
    for error, raw_score in zip(errors, scores):
        score = float(np.clip(raw_score, 0.0, 1.0))
        status = "ANOMALY" if score >= 0.65 else "NORMAL"
        output.append(DeepLearningResult(
            True, score, status,
            "Neural autoencoder found an unusual invoice pattern." if status == "ANOMALY"
            else "Invoice pattern is within the learned normal range.",
            float(error),
        ))
    return output
