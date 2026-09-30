import pandas as pd

from src.deep_learning import score_invoices


def _batch(n=12):
    return pd.DataFrame([
        {
            "invoice_id": f"DL{i:03d}",
            "vendor": f"Vendor {i % 3}",
            "amount": 1000 + (i % 4) * 250,
            "category": ["Office", "IT", "Travel", "Food"][i % 4],
            "invoice_date": f"2026-09-{(i % 20) + 1:02d}",
        }
        for i in range(n)
    ])


def test_deep_learning_detector_returns_one_result_per_invoice():
    df = _batch()
    results = score_invoices(
        df,
        {"Office": 10000, "IT": 10000, "Travel": 15000, "Food": 5000},
    )
    assert len(results) == len(df)
    assert all(0.0 <= result.score <= 1.0 for result in results)
    assert all(result.available for result in results)


def test_deep_learning_detector_is_deterministic():
    df = _batch()
    limits = {"Office": 10000, "IT": 10000, "Travel": 15000, "Food": 5000}
    first = score_invoices(df, limits)
    second = score_invoices(df, limits)
    assert [round(x.score, 6) for x in first] == [round(x.score, 6) for x in second]


def test_deep_learning_detector_safe_for_tiny_batch():
    df = _batch(1)
    results = score_invoices(df, {"Office": 10000})
    assert results[0].available is False
    assert results[0].status == "UNAVAILABLE"
