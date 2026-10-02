# FinSight Copilot

FinSight Copilot is an evidence-first AP analyst, not a generic chatbot.

## Architecture

User -> intent/context -> deterministic tools -> trusted evidence -> AI explanation -> optional confirmed action -> audit event.

The Python rule engine remains the source of truth for invoice validation. Gemini is an explanation/reasoning layer and must never invent invoice facts or override deterministic results.

## Current Copilot tools

- get_invoice
- search_invoices
- get_exceptions
- get_review_queue
- find_potential_duplicates
- explain_invoice
- get_statistics
- build_tool_context

## Safety model

The Copilot may explain and recommend. State-changing invoice actions must be explicit, confirmed by the user, and written to the audit trail.

Never:
- invent invoice/vendor/amount/date/audit information;
- call an invoice fraudulent without evidence;
- silently approve or reject an invoice;
- present an AI-generated guess as a deterministic validation result.

## Context

The UI may provide a current invoice. If the user asks "why?", "is this a duplicate?", or "what should I check?" the Copilot should use that current invoice context without requiring the user to repeat its ID.

## Future action tools

The next extension should expose controlled application actions such as:

- send_to_human_review
- request_information
- approve_invoice
- reject_invoice

These actions must require confirmation and must persist an audit event after successful execution.
