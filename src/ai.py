import json, os
from dotenv import load_dotenv
load_dotenv()

def _trusted_payload(results):
    return [{
        "invoice_id": r["invoice_id"],
        "status": r["status"],
        "human_review_required": r["human_review_required"],
        "rule_ids": r["rule_ids"],
        "reasons": r["reasons"],
        "evidence": r["evidence"],
    } for r in results]

def build_chat_prompt(question, results):
    trusted = _trusted_payload(results)
    return f"""You are FinSight, an Accounts-Payable exception assistant.
Answer the user's question using ONLY the trusted invoice analysis below.

Rules:
- Never invent invoice facts, values, vendors, dates, rules, or review actions.
- Never change a deterministic decision.
- If the data does not contain the answer, say so.
- Be concise and useful to an accounts-payable reviewer.
- When discussing an invoice, name the invoice_id.
- Distinguish AUTO-PASS, EXCEPTION, and HUMAN REVIEW.
- For flags, explain the exact rule/evidence behind them.

USER QUESTION:
{question}

TRUSTED INVOICE ANALYSIS:
{json.dumps(trusted, indent=2, default=str)}

Return plain text only."""

def template_chat(question, results):
    q = question.lower()
    if not results:
        return "No invoice analysis is loaded yet. Upload a CSV and analyze it first."
    if "human" in q and "review" in q:
        ids = [r["invoice_id"] for r in results if r["human_review_required"]]
        return "Invoices requiring human review: " + (", ".join(map(str, ids)) if ids else "none.")
    if "exception" in q or "flag" in q:
        flagged = [r for r in results if r["status"] == "EXCEPTION"]
        if not flagged:
            return "No deterministic exceptions were found."
        return "\n".join(
            f"{r['invoice_id']}: {', '.join(x['message'] for x in r['reasons'])}"
            for r in flagged
        )
    for r in results:
        iid = str(r["invoice_id"]).lower()
        if iid and iid in q:
            if r["status"] == "CLEAN":
                return f"{r['invoice_id']} passed all deterministic checks."
            return f"{r['invoice_id']} is {('in human review' if r['human_review_required'] else 'an exception')}: " + " ".join(x["message"] for x in r["reasons"])
    return f"I can answer questions about the {len(results)} analyzed invoices, their rules, evidence, exceptions, and review routing. I could not find a direct answer to that question in the trusted data."

def ask_gemini(question, results):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return template_chat(question, results), "template_fallback"
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=build_chat_prompt(question, results),
        )
        text = (response.text or "").strip()
        if not text:
            raise ValueError("Gemini returned an empty response.")
        return text, "gemini"
    except Exception as exc:
        return template_chat(question, results), f"template_fallback: {type(exc).__name__}"

def explain_invoice(result):
    if result["status"] == "CLEAN":
        return f"{result['invoice_id']} passed all configured checks. No deterministic rule violations were found."
    parts = []
    for reason in result["reasons"]:
        parts.append(reason["message"])
    route = "human review" if result["human_review_required"] else "exception handling"
    return f"{result['invoice_id']} was routed to {route}: " + " ".join(parts)
