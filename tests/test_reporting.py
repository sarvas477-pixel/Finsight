import pandas as pd
from src import persistence
from src.reporting import VIEWS, attach_reviews, filter_results, view_counts
from src.rule_engine import process_invoices

def _frame():
    results=process_invoices(pd.read_csv("data/invoices.csv"))
    return pd.DataFrame([{
        "invoice_id":r["invoice_id"],"vendor":r["evidence"]["vendor"],"status":r["status"],
        "route":r["route"],"human_review_required":r["human_review_required"],
        "rule_ids":", ".join(r["rule_ids"])
    } for r in results])

def test_views_and_counts():
    df=_frame()
    assert view_counts(df)=={"All":5,"Auto-pass":2,"Exceptions":3,"Human review":3}
    assert set(view_counts(df))==set(VIEWS)

def test_filter_by_view():
    df=_frame()
    assert list(filter_results(df,"","Auto-pass").invoice_id)==["INV001","INV004"]
    assert list(filter_results(df,"","Exceptions").invoice_id)==["INV002","INV003","INV005"]
    assert len(filter_results(df,"","nonsense"))==5

def test_search_is_case_insensitive_and_literal():
    df=_frame()
    assert list(filter_results(df,"amount_limit").invoice_id)==["INV002"]
    assert list(filter_results(df,"  abc suppliers ").invoice_id)==["INV001","INV003"]
    assert filter_results(df,"(").empty
    assert list(filter_results(df,"abc","Exceptions").invoice_id)==["INV003"]

def test_attach_reviews():
    df=_frame()
    out=attach_reviews(df,{"INV003":{"action":"REJECTED","comment":"dup"}})
    assert out.loc[out.invoice_id=="INV003","reviewer_decision"].item()=="REJECTED"
    assert out.loc[out.invoice_id=="INV001","reviewer_decision"].item()==""
    assert "reviewer_decision" not in df.columns

class _FakeTable:
    def __init__(self,sink): self.sink=sink
    def insert(self,rows): self.sink.append(rows); return self
    def execute(self): return self

class _FakeClient:
    def __init__(self): self.batches=[]
    def table(self,name):
        assert name=="audit_events"
        return _FakeTable(self.batches)

def test_batch_insert_chunks_and_single_timestamp():
    fake=_FakeClient()
    original=persistence._client
    persistence._client=lambda:fake
    try:
        events=[{"event_type":"DECISION","invoice_id":i,"message":"x"} for i in range(1200)]
        ok,msg=persistence.save_audit_events(events)
        assert ok and len(fake.batches)==3 and [len(x) for x in fake.batches]==[500,500,200]
        timestamps={row["created_at"] for batch in fake.batches for row in batch}
        assert len(timestamps)==1
    finally:
        persistence._client=original
