"""FinSight Copilot data tools.

The rule engine remains the source of truth. This module lets the AI decide how
to present/query already-analysed invoice data, while Python executes the
actual operation so tables and charts are truthful.
"""
from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd


def results_frame(results: list[dict[str, Any]] | None) -> pd.DataFrame:
    rows = []
    for r in results or []:
        evidence = r.get("evidence") or {}
        rows.append({
            "invoice_id": r.get("invoice_id"),
            "vendor": evidence.get("vendor"),
            "amount": evidence.get("amount"),
            "category": evidence.get("category"),
            "invoice_date": evidence.get("invoice_date"),
            "status": r.get("status"),
            "route": r.get("route"),
            "confidence": float(r.get("confidence", 0)),
            "human_review_required": bool(r.get("human_review_required")),
            "rule_ids": ", ".join(r.get("rule_ids") or []),
            "reasons": " | ".join(str(x.get("message", "")) for x in r.get("reasons", [])),
            "matched_invoice_id": evidence.get("matched_invoice_id"),
        })
    return pd.DataFrame(rows)


def _heuristic_plan(question: str) -> dict[str, Any]:
    q = " ".join(str(question or "").lower().split())
    wants_chart = any(x in q for x in ("graph", "chart", "plot", "visualize", "visualise"))
    wants_table = any(x in q for x in ("table", "tabular", "show all", "show the results", "list all"))
    if wants_chart:
        output = "chart"
    elif wants_table:
        output = "table"
    else:
        output = "answer"

    operation = "all"
    if any(x in q for x in ("exception", "exceptions", "flagged", "failed")):
        operation = "exceptions"
    elif any(x in q for x in ("human review", "needs review", "review queue")):
        operation = "human_review"
    elif any(x in q for x in ("auto-pass", "autopass", "clean invoices", "passed invoices")):
        operation = "auto_pass"

    group_by = None
    for candidate in ("category", "vendor", "status", "route", "invoice_date"):
        if candidate in q and any(x in q for x in ("by ", "per ", "each ", "group", "over time", "trend")):
            group_by = candidate
            break
    if output == "chart" and group_by is None:
        group_by = "category" if "category" in q else "status"

    columns = []
    aliases = {
        "invoice id": "invoice_id", "invoice": "invoice_id", "vendor": "vendor",
        "amount": "amount", "category": "category", "date": "invoice_date",
        "invoice date": "invoice_date", "status": "status", "route": "route",
        "confidence": "confidence", "rule": "rule_ids", "reason": "reasons",
    }
    for phrase, col in aliases.items():
        if phrase in q and col not in columns:
            columns.append(col)

    aggregation = "sum" if any(x in q for x in ("total spend", "total amount", "sum", "spend")) else ("average" if "average" in q else "count")
    return {
        "output": output,
        "operation": operation,
        "group_by": group_by,
        "aggregation": aggregation,
        "columns": columns,
        "sort_by": None,
        "descending": True,
        "limit": 500,
        "title": "FinSight results",
        "aggregation": "count",
    }


def plan_with_gemini(question: str, results: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            return None
        from google import genai
        client = genai.Client(api_key=key)
        model = os.getenv("GEMINI_MODEL") or "gemini-3.6-flash"
        schema = {
            "type": "object",
            "properties": {
                "output": {"type": "string", "enum": ["answer", "table", "chart"]},
                "operation": {"type": "string", "enum": ["all", "exceptions", "human_review", "auto_pass"]},
                "group_by": {"type": ["string", "null"], "enum": ["invoice_id", "vendor", "category", "invoice_date", "status", "route", None]},
                "columns": {"type": "array", "items": {"type": "string", "enum": [
                    "invoice_id", "vendor", "amount", "category", "invoice_date", "status",
                    "route", "confidence", "human_review_required", "rule_ids", "reasons", "matched_invoice_id"
                ]}},
                "sort_by": {"type": ["string", "null"]},
                "descending": {"type": "boolean"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500},
                "title": {"type": "string"},
                "aggregation": {"type": "string", "enum": ["count", "sum", "average", "min", "max"]},
            },
            "required": ["output", "operation", "group_by", "columns", "sort_by", "descending", "limit", "title", "aggregation"],
        }
        sample = results_frame(results).head(30).to_dict(orient="records")
        prompt = f"""You are the command planner inside FinSight.
Turn the user's natural-language request into a safe data presentation/query plan.
The Python executor will perform the operation. Never invent invoice facts.
Use output=table when the user asks to show/list/display data, output=chart for graph/chart requests.
Choose group_by when the user asks for a breakdown, such as 'by category' or 'over time'.
Only use the supplied column names.
USER: {question}
AVAILABLE COLUMNS: {list(results_frame(results).columns)}
SAMPLE DATA: {json.dumps(sample, default=str)}
"""
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": schema,
            },
        )
        return json.loads(response.text)
    except Exception:
        return None


def execute_plan(plan: dict[str, Any], results: list[dict[str, Any]] | None) -> dict[str, Any]:
    df = results_frame(results)
    if df.empty:
        return {"output": plan.get("output", "answer"), "answer": "No analyzed invoice data is loaded yet. Upload a CSV and run Analyze first."}

    operation = plan.get("operation", "all")
    if operation == "exceptions":
        df = df[df["status"].eq("EXCEPTION")]
    elif operation == "human_review":
        df = df[df["human_review_required"].astype(bool)]
    elif operation == "auto_pass":
        df = df[df["route"].eq("AUTO_PASS")]

    group_by = plan.get("group_by")
    output = plan.get("output", "table")

    if group_by and group_by in df.columns:
        if output == "chart":
            aggregation = plan.get("aggregation", "count")
            if aggregation == "sum" and "amount" in df.columns:
                chart = df.groupby(group_by, dropna=False)["amount"].sum().sort_values(ascending=False).to_frame("total_amount")
            elif aggregation == "average" and "amount" in df.columns:
                chart = df.groupby(group_by, dropna=False)["amount"].mean().sort_values(ascending=False).to_frame("average_amount")
            else:
                chart = df.groupby(group_by, dropna=False).size().sort_values(ascending=False).to_frame("invoice_count")
            return {
                "output": "chart",
                "title": plan.get("title") or f"FinSight breakdown by {group_by}",
                "data": chart.reset_index(),
                "x": group_by,
                "y": chart.columns[0],
                "answer": f"Here is the requested breakdown by {group_by}.",
            }
        aggregation = plan.get("aggregation", "count")
        if aggregation == "sum" and "amount" in df.columns:
            grouped = df.groupby(group_by, dropna=False)["amount"].sum().reset_index(name="total_amount")
        elif aggregation == "average" and "amount" in df.columns:
            grouped = df.groupby(group_by, dropna=False)["amount"].mean().reset_index(name="average_amount")
        else:
            grouped = df.groupby(group_by, dropna=False).size().reset_index(name="invoice_count")
        return {"output": "table", "title": plan.get("title") or f"Results by {group_by}", "data": grouped}

    columns = [c for c in plan.get("columns", []) if c in df.columns]
    if not columns:
        columns = list(df.columns)

    out = df[columns].copy()
    sort_by = plan.get("sort_by")
    if sort_by in out.columns:
        out = out.sort_values(sort_by, ascending=not bool(plan.get("descending", True)))

    out = out.head(int(plan.get("limit", 500)))
    if output == "chart":
        numeric = [c for c in out.columns if pd.api.types.is_numeric_dtype(out[c])]
        if numeric:
            chart_df = out[numeric].copy()
            chart_df.index = out["invoice_id"].astype(str) if "invoice_id" in out.columns else chart_df.index
            return {"output": "chart", "title": plan.get("title") or "FinSight chart", "data": chart_df, "answer": "Here is the requested chart."}
        counts = out["status"].value_counts().to_frame("invoice_count") if "status" in out.columns else pd.DataFrame()
        return {"output": "chart", "title": plan.get("title") or "FinSight chart", "data": counts, "answer": "Here is the requested chart."}

    return {"output": "table", "title": plan.get("title") or "FinSight results", "data": out,
            "answer": f"Showing {len(out)} result(s) from the analyzed FinSight dataset."}


def copilot_command(question: str, results: list[dict[str, Any]] | None) -> dict[str, Any]:
    heuristic = _heuristic_plan(question)
    plan = plan_with_gemini(question, results) or heuristic
    # Deterministic presentation requests must always work, even without Gemini.
    if heuristic["output"] in {"table", "chart"}:
        if not plan.get("output") or plan.get("output") == "answer":
            plan.update(heuristic)
    result = execute_plan(plan, results)
    result["mode"] = "ai_plan" if plan is not heuristic else "local_plan"
    return result
