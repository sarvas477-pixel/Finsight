def build_results_df(results):
    return pd.DataFrame([{"invoice_id":r.get("invoice_id"),"vendor":(r.get("evidence") or {}).get("vendor"),
        "amount":(r.get("evidence") or {}).get("amount"),"category":(r.get("evidence") or {}).get("category"),
        "invoice_date":(r.get("evidence") or {}).get("invoice_date"),"status":r.get("status"),"route":r.get("route"),
        "confidence":float(r.get("confidence",0)),"human_review_required":bool(r.get("human_review_required",False)),
        "dl_anomaly_score":r.get("dl_anomaly_score"),"dl_anomaly_flag":bool(r.get("dl_anomaly_flag",False)),"ai_risk_score":float(r.get("ai_risk_score",0)),
        "rule_ids":", ".join(r.get("rule_ids") or []),"reasons":" | ".join(str(x.get("message","")) for x in r.get("reasons",[])),
        "matched_invoice_id":(r.get("evidence") or {}).get("matched_invoice_id")} for r in results])
