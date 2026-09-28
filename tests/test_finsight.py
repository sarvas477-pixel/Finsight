import pandas as pd
import pytest
from src.rule_engine import process_invoices, summarize_results
from src.ai import template_chat, build_chat_prompt

def inv(**over):
    x={"invoice_id":"T1","vendor":"Vendor","amount":5000,"category":"IT","invoice_date":"2026-09-10"}
    x.update(over); return x

def rules(r): return [x["rule"] for x in r["reasons"]]

def test_clean():
    r=process_invoices(pd.DataFrame([inv()]))[0]
    assert r["status"]=="CLEAN" and not r["human_review_required"]

def test_missing_vendor():
    r=process_invoices(pd.DataFrame([inv(vendor="")]))[0]
    assert "MISSING_REQUIRED_FIELD" in rules(r)

def test_limit():
    r=process_invoices(pd.DataFrame([inv(amount=15001,category="Travel")]))[0]
    assert "AMOUNT_LIMIT" in rules(r)

def test_invalid_amount():
    r=process_invoices(pd.DataFrame([inv(amount=-1)]))[0]
    assert "INVALID_AMOUNT" in rules(r)

def test_invalid_date():
    r=process_invoices(pd.DataFrame([inv(invoice_date="bad")]))[0]
    assert "INVALID_DATE" in rules(r)

def test_unknown_category():
    r=process_invoices(pd.DataFrame([inv(category="Random")]))[0]
    assert "UNKNOWN_CATEGORY" in rules(r)

def test_duplicate_id():
    rs=process_invoices(pd.DataFrame([inv(invoice_id="A"),inv(invoice_id="A")]))
    assert rs[0]["status"]=="CLEAN" and "DUPLICATE_INVOICE_ID" in rules(rs[1])

def test_content_duplicate():
    rs=process_invoices(pd.DataFrame([inv(invoice_id="A",vendor="ABC",amount=4500,category="Travel",invoice_date="2026-09-14"),
                                      inv(invoice_id="B",vendor="ABC",amount=4500,category="Travel",invoice_date="2026-09-14")]))
    assert "DUPLICATE_INVOICE" in rules(rs[1])
    assert rs[1]["reasons"][-1]["matched_invoice_id"]=="A"

def test_duplicate_columns():
    df=pd.DataFrame([["A","V",1,"IT","IT2","2026-01-01"]],columns=["invoice_id","vendor","amount","category","amount","invoice_date"])
    with pytest.raises(ValueError,match="Duplicate CSV columns"):
        process_invoices(df)

def test_missing_columns():
    with pytest.raises(ValueError,match="Missing required CSV columns"):
        process_invoices(pd.DataFrame([{"invoice_id":"A"}]))

def test_summary():
    rs=process_invoices(pd.DataFrame([inv(),inv(invoice_id="B",vendor="")]))
    s=summarize_results(rs)
    assert s=={"total":2,"clean":1,"exceptions":0,"review_required":1}

def test_template_chat():
    rs=process_invoices(pd.read_csv("data/invoices.csv"))
    answer=template_chat("Which invoices need human review?",rs)
    assert "INV003" in answer and "INV005" in answer

def test_prompt_is_grounded():
    rs=process_invoices(pd.DataFrame([inv(invoice_id="A")]))
    p=build_chat_prompt("Why is A clean?",rs)
    assert "TRUSTED INVOICE ANALYSIS" in p and "A" in p
