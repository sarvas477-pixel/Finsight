"""Trainable invoice risk model for FinSight.

The model is a supervised RandomForest classifier over engineered invoice
features. It can train from labelled CSV data with a target column named
risk_label (0/1). If no labelled dataset exists, the trainer can generate
weak labels from the deterministic rule engine; those labels are explicitly
marked as weak supervision in the model metadata.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

MODEL_VERSION = "1.0.0"
DEFAULT_MODEL_PATH = Path("models/finsight_risk.joblib")
CATEGORIES = ["Office", "IT", "Travel", "Food", "Equipment", "Other"]


def make_features(df: pd.DataFrame, category_limits: dict[str, float]) -> pd.DataFrame:
    x = pd.DataFrame(index=df.index)
    x["amount"] = pd.to_numeric(df.get("amount"), errors="coerce").fillna(0)
    x["log_amount"] = np.log1p(x["amount"].clip(lower=0))
    x["category_limit"] = df.get("category", "").map(category_limits).fillna(0) if hasattr(df.get("category", ""), "map") else 0
    x["limit_ratio"] = np.where(x["category_limit"] > 0, x["amount"] / x["category_limit"], x["amount"] / 10000)
    x["vendor_missing"] = df.get("vendor", "").fillna("").astype(str).str.strip().eq("").astype(int)
    dates = pd.to_datetime(df.get("invoice_date"), errors="coerce")
    x["day"] = dates.dt.day.fillna(0)
    x["weekday"] = dates.dt.dayofweek.fillna(-1) + 1
    x["month"] = dates.dt.month.fillna(0)
    x["category_code"] = df.get("category", "").fillna("Other").astype(str).str.strip().str.casefold().map(
        {c.casefold(): i for i, c in enumerate(CATEGORIES)}
    ).fillna(len(CATEGORIES))
    vendors = df.get("vendor", "").fillna("").astype(str).str.strip().str.casefold()
    x["vendor_frequency"] = vendors.map(vendors.value_counts()).fillna(0)
    return x.fillna(0).astype(float)


def weak_labels(df: pd.DataFrame, category_limits: dict[str, float]) -> pd.Series:
    amount = pd.to_numeric(df.get("amount"), errors="coerce").fillna(0)
    category = df.get("category", "").fillna("").astype(str).str.strip()
    vendor_missing = df.get("vendor", "").fillna("").astype(str).str.strip().eq("")
    limit = category.map(category_limits).fillna(np.inf)
    return ((vendor_missing) | (amount > limit)).astype(int)


def train_model(
    df: pd.DataFrame,
    category_limits: dict[str, float],
    model_path: str | Path = DEFAULT_MODEL_PATH,
    label_column: str = "risk_label",
) -> dict[str, Any]:
    labels_source = "labelled"
    if label_column not in df.columns:
        y = weak_labels(df, category_limits)
        labels_source = "weak_rules"
    else:
        y = pd.to_numeric(df[label_column], errors="coerce").fillna(0).astype(int).clip(0, 1)

    if len(df) < 20:
        raise ValueError("At least 20 labelled/weakly-labelled invoices are required to train the model.")
    if y.nunique() < 2:
        raise ValueError("Training data must contain both clean (0) and risky (1) examples.")

    X = make_features(df, category_limits)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    meta = {
        "model_version": MODEL_VERSION,
        "model_type": "RandomForestClassifier",
        "labels_source": labels_source,
        "rows": len(df),
        "accuracy": float(accuracy_score(y_test, pred)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "features": list(X.columns),
    }
    path = Path(model_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "metadata": meta}, path)
    path.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def predict(
    df: pd.DataFrame,
    category_limits: dict[str, float],
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> list[dict[str, Any]]:
    path = Path(model_path)
    if not path.exists():
        return [{"available": False, "risk_score": 0.0, "reason": "Trained model is not available."} for _ in range(len(df))]
    try:
        bundle = joblib.load(path)
        model = bundle["model"]
        scores = model.predict_proba(make_features(df, category_limits))[:, 1]
        return [
            {
                "available": True,
                "risk_score": round(float(score), 4),
                "status": "HIGH_RISK" if score >= 0.65 else "LOW_RISK",
                "reason": "Trained AI model estimates elevated invoice risk." if score >= 0.65 else "Trained AI model estimates low invoice risk.",
            }
            for score in scores
        ]
    except Exception as exc:
        return [{"available": False, "risk_score": 0.0, "reason": f"Trained model unavailable: {exc}"} for _ in range(len(df))]
