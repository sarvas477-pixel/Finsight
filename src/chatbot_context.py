"""Build bounded, grounded context for the FinSight chatbot."""
import json
from .chatbot_tools import RULE_CATALOG, find_duplicates, find_mentioned_invoices, get_auto_pass, get_exceptions, get_human_review, get_summary, invoice_label, public_invoice_view, rule_counts
MAX_FOCUS_INVOICES = 10

def _category_limits():
    try:
        from .config import CATEGORY_LIMITS
        return CATEGORY_LIMITS
    except ImportError:
        return {}

def build_chat_context_dict(results, max_items=40, question=""):
    items=list(results or []); by_id={str(x.get("invoice_id", "")).strip().casefold(): x for x in items}; focus=[]; seen=set()
    for item in find_mentioned_invoices(items, question):
        related=[item]+[by_id[str(m).strip().casefold()] for m in item.get("matched_invoice_ids", []) or [] if str(m).strip().casefold() in by_id]
        for candidate in related:
            key=invoice_label(candidate).casefold()
            if key not in seen and len(focus)<MAX_FOCUS_INVOICES: seen.add(key); focus.append(public_invoice_view(candidate))
    passed=get_auto_pass(items, 10**9); summary=get_summary(items)
    return {"summary":summary,"rule_counts":rule_counts(items),"rule_catalog":RULE_CATALOG,"category_limits":_category_limits(),"focus_invoices":focus,"exceptions":[public_invoice_view(x) for x in get_exceptions(items,max_items)],"human_review":[public_invoice_view(x) for x in get_human_review(items,max_items)],"duplicates":[public_invoice_view(x) for x in find_duplicates(items,max_items)],"auto_pass_ids":[invoice_label(x) for x in passed[:100]],"truncated":{"exceptions":max(0,summary["exceptions"]-max_items),"human_review":max(0,summary["human_review"]-max_items),"auto_pass_ids":max(0,len(passed)-100)}}

def build_chat_context(results, max_items=40, question=""):
    return json.dumps(build_chat_context_dict(results,max_items,question), default=str, indent=2)
