import pandas as pd
from src.trained_ai import train_model, predict

LIMITS = {"Office": 10000, "IT": 10000, "Travel": 15000, "Food": 5000}

def test_train_and_predict(tmp_path):
    df = pd.read_csv("data/training_invoices.csv")
    path = tmp_path / "risk.joblib"
    meta = train_model(df, LIMITS, path)
    assert meta["rows"] == 40
    assert path.exists()
    out = predict(df.head(3), LIMITS, path)
    assert len(out) == 3
    assert all(x["available"] for x in out)
    assert all(0 <= x["risk_score"] <= 1 for x in out)
