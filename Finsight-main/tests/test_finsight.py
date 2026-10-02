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
    assert s=={"total":2,"clean":1,"exceptions":1,"review_required":1}

def test_template_chat():
    rs=process_invoices(pd.read_csv("data/invoices.csv"))
    answer=template_chat("Which invoices need human review?",rs)
    assert "INV003" in answer and "INV005" in answer

def test_prompt_is_grounded():
    rs=process_invoices(pd.DataFrame([inv(invoice_id="A")]))
    p=build_chat_prompt("Why is A clean?",rs)
    assert "TRUSTED INVOICE ANALYSIS" in p and "A" in p

@pytest.mark.parametrize("amount,category,expected", [
    (1, "Food", "CLEAN"), (5000, "Food", "CLEAN"), (5001, "Food", "EXCEPTION"),
    (10000, "IT", "CLEAN"), (10001, "IT", "EXCEPTION"), (15000, "Travel", "CLEAN"),
    (15001, "Travel", "EXCEPTION"), (10000, "Equipment", "CLEAN"), (10001, "Equipment", "EXCEPTION"),
    (9999, "Office", "CLEAN"), (10001, "Office", "EXCEPTION"),
])
def test_boundary_limits(amount, category, expected):
    r = process_invoices(pd.DataFrame([inv(amount=amount, category=category)]))[0]
    assert r["status"] == expected

@pytest.mark.parametrize("bad_date", ["", "not-a-date", "2026-99-99", "abc", None])
def test_bad_dates(bad_date):
    r = process_invoices(pd.DataFrame([inv(invoice_date=bad_date)]))[0]
    if bad_date in ("", None):
        assert "MISSING_REQUIRED_FIELD" in rules(r)
    else:
        assert "INVALID_DATE" in rules(r)

@pytest.mark.parametrize("bad_amount", [0, -1, "abc", "", None, float("inf"), float("nan")])
def test_bad_amounts(bad_amount):
    r = process_invoices(pd.DataFrame([inv(amount=bad_amount)]))[0]
    if bad_amount in ("", None) or (isinstance(bad_amount, float) and pd.isna(bad_amount)):
        assert "MISSING_REQUIRED_FIELD" in rules(r)
    else:
        assert "INVALID_AMOUNT" in rules(r)

def test_route_and_confidence_are_present():
    clean = process_invoices(pd.DataFrame([inv()]))[0]
    review = process_invoices(pd.DataFrame([inv(vendor="")]))[0]
    assert clean["route"] == "AUTO_PASS" and clean["confidence"] == 1.0
    assert review["route"] == "HUMAN_REVIEW" and 0 < review["confidence"] <= 1

def test_ai_common_summary():
    rs = process_invoices(pd.DataFrame([inv(), inv(invoice_id="B", vendor="")]))
    answer = template_chat("Give me a summary count", rs)
    assert "2 invoices" in answer and "1 AUTO-PASS" in answer and "require HUMAN REVIEW" in answer

@pytest.mark.parametrize("idx", list(range(1, 21)))
def test_generated_invoice_batch(idx):
    row = inv(invoice_id=f"B{idx:03d}", amount=100 + idx, vendor=f"Vendor {idx}")
    r = process_invoices(pd.DataFrame([row]))[0]
    assert r["status"] == "CLEAN"
    assert r["route"] == "AUTO_PASS"


def test_sample_csv_exact_summary():
    rs = process_invoices(pd.read_csv("data/invoices.csv"))
    assert summarize_results(rs) == {
        "total": 5,
        "clean": 2,
        "exceptions": 3,
        "review_required": 3,
    }
    by_id = {r["invoice_id"]: r for r in rs}
    assert by_id["INV001"]["status"] == "CLEAN"
    assert by_id["INV002"]["rule_ids"] == ["AMOUNT_LIMIT"]
    assert by_id["INV003"]["rule_ids"] == ["DUPLICATE_INVOICE"]
    assert by_id["INV005"]["rule_ids"] == ["MISSING_REQUIRED_FIELD"]
