def create_prompt(result):

    prompt = f"""
You are an Accounts Payable audit explanation assistant.

Explain why the invoice was flagged based ONLY on the evidence provided.

Do not invent or assume any information.
Do not change or override the rule-engine decision.

Invoice ID: {result["invoice_id"]}
Decision: {result["status"]}

Reasons:
{result["reasons"]}

Evidence:
{result["evidence"]}

Return a short, clear explanation for a human reviewer.
"""

    return prompt