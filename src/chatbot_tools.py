"""Safe query helpers over deterministic FinSight results."""
import math
import re
MAX_FIELD_CHARS=120
RULE_CATALOG={"MISSING_REQUIRED_FIELD":"A required invoice field is blank.","DUPLICATE_INVOICE_ID":"The same invoice ID appears more than once.","INVALID_AMOUNT":"The amount is missing, invalid, or not greater than zero.","INVALID_DATE":"The invoice date is missing or invalid.","UNKNOWN_CATEGORY":"The category is not configured.","AMOUNT_LIMIT":"The amount exceeds its category limit.","DUPLICATE_INVOICE":"Another invoice has matching content."}
_TOKEN=re.compile(r"[\w\-]+")
def _items(results): return list(results or [])
def _clip(value,limit=MAX_FIELD_CHARS): return value[:limit]+"…" if isinstance(value,str) and len(value)>limit else value
def invoice_id_of(item):
    value=item.get("invoice_id")
    if value is None or (isinstance(value,float) and math.isnan(value)): return None
    text=str(value).strip(); return None if text.casefold() in {"","nan","none"} else text
def invoice_label(item): return invoice_id_of(item) or "(no invoice ID)"
def get_invoice(results,invoice_id):
    wanted=str(invoice_id).strip().casefold(); return next((x for x in _items(results) if (invoice_id_of(x) or "").casefold()==wanted),None)
def find_mentioned_invoices(results,question):
    index={invoice_id_of(x).casefold():x for x in _items(results) if invoice_id_of(x)}; found=[]; seen=set()
    for token in _TOKEN.findall(str(question or "")):
        key=token.strip("-_").casefold()
        if key in index and key not in seen: seen.add(key); found.append(index[key])
    return found
def get_summary(results):
    items=_items(results); count=lambda route:sum(str(x.get("route","")).upper()==route for x in items)
    return {"total":len(items),"auto_pass":count("AUTO_PASS"),"exceptions":count("EXCEPTION"),"human_review":count("HUMAN_REVIEW")}
def rule_counts(results):
    counts={}
    for item in _items(results):
        for rule in item.get("rule_ids",[]) or []: counts[rule]=counts.get(rule,0)+1
    return counts
def known_rule_ids(results): return set(RULE_CATALOG)|set(rule_counts(results))
def _by_route(results,route,limit): return [x for x in _items(results) if str(x.get("route","")).upper()==route][:limit]
def get_exceptions(results,limit=25): return _by_route(results,"EXCEPTION",limit)
def get_human_review(results,limit=25): return _by_route(results,"HUMAN_REVIEW",limit)
def get_auto_pass(results,limit=25): return _by_route(results,"AUTO_PASS",limit)
def get_by_rule(results,rule_ids,limit=25):
    wanted=set(rule_ids); return [x for x in _items(results) if wanted & set(x.get("rule_ids",[]) or [])][:limit]
def find_duplicates(results,limit=25): return [x for x in _items(results) if any("DUPLICATE" in str(r) for r in x.get("rule_ids",[]) or []) or x.get("matched_invoice_ids")][:limit]
def public_invoice_view(item):
    if not item:return None
    keys=("invoice_id","vendor","amount","category","invoice_date","decision","route","confidence","review_reason","rule_ids","matched_invoice_ids","explanation")
    view={k:_clip(item[k],400 if k=="explanation" else MAX_FIELD_CHARS) for k in keys if k in item}
    if "rule_details" in item:view["rule_details"]=[{"rule":d.get("rule"),"message":_clip(d.get("message")),"actual_value":_clip(d.get("actual_value")),"expected_value":_clip(d.get("expected_value"))} for d in item["rule_details"]]
    if "evidence_used" in item:view["evidence_used"]={k:_clip(v) for k,v in (item["evidence_used"] or {}).items()}
    return view
