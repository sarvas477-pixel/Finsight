# FinSight AI Stack

FinSight now uses a hybrid invoice intelligence pipeline:

1. Deterministic policy rules — required fields, limits, duplicates and evidence.
2. Supervised trained AI — RandomForest risk classifier trained from labelled invoice data.
3. Deep learning — neural autoencoder for unsupervised anomaly detection.
4. Hybrid risk — combines model signals without allowing AI to silently bypass policy rules.
5. Human review — high-risk or uncertain invoices are routed for review.
6. Gemini Copilot — natural-language explanations and workflow assistance.

## Train the model

```bash
python scripts/train_ai.py data/training_invoices.csv
```

For real deployment, replace the demo training CSV with historical reviewed invoices and a verified risk_label column. Do not treat weak rule-derived labels as ground truth.

## Model signals

- ai_risk_score: supervised classifier probability of risk.
- dl_anomaly_score: neural reconstruction-based anomaly score.
- hybrid_risk_score: combined AI signal.
- hybrid_status: LOW_RISK or HIGH_RISK.
- DL_ANOMALY: evidence item when the neural model finds an unusual pattern.

AI is advisory. Deterministic policy rules and human review remain the final control layer.
