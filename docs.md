# FinSight — Days 16–20 completion notes

## Day 16 — Full testing
- Rule-engine tests cover clean invoices, missing fields, limits, invalid amounts/dates, unknown categories, duplicate IDs, content duplicates, malformed columns, summaries, and AI grounding.
- The test suite is designed to be expanded with generated 50+ invoice fixtures; `pytest -q` is the release gate.
- AI deterministic intent handlers are tested separately from Gemini, so API outages do not block the demo.

## Day 17 — Enterprise polish
- Configurable category limits remain in `src/config.py`.
- Each result now carries `route` and `confidence` metadata.
- Evidence is preserved alongside every rule violation.
- Dashboard includes filtering, metrics, review workflow, evidence, exports, and an AI assistant.

## Day 18 — Deployment/documentation
- Local run instructions are in `README.md`.
- Optional Supabase schema is in `supabase_schema.sql`.
- Secrets belong in `.env`, never in GitHub.
- Streamlit Community Cloud is the intended Python dashboard deployment path.

## Day 19 — Presentation
Recommended demo flow:
1. Upload the sample CSV.
2. Analyze it and show the KPI cards.
3. Open Exceptions and explain one rule/evidence pair.
4. Ask FinSight AI: "Which invoices need human review?"
5. Ask: "Why is INV003 in human review?"
6. Approve/reject one review item with a comment.
7. Show the audit log and download the report.

## Day 20 — Final submission checklist
- [ ] `pytest -q` passes.
- [ ] No `.env` or real credentials are committed.
- [ ] Sample CSV produces deterministic results.
- [ ] Gemini key is configured only through environment variables for live AI.
- [ ] Human review actions are demonstrated.
- [ ] Results and audit exports are downloaded once during rehearsal.
- [ ] GitHub main branch contains the tested version.
