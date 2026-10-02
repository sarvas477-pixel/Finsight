from src.copilot_tools import (
    build_tool_context,
    explain_invoice,
    find_potential_duplicates,
    get_review_queue,
    get_statistics,
)


def sample_results():
    return [
        {
            "invoice_id": "INV001",
            "status": "CLEAN",
            "route": "AUTO_PASS",
            "confidence": 1.0,
            "human_review_required": False,
            "rule_ids": [],
            "reasons": [],
            "evidence": {
                "invoice_id": "INV001",
                "vendor": "ABC Suppliers",
                "amount": 4500,
                "category": "Travel",
                "invoice_date": "2026-09-14",
            },
        },
        {
            "invoice_id": "INV005",
            "status": "EXCEPTION",
            "route": "HUMAN_REVIEW",
            "confidence": 0.95,
            "human_review_required": True,
            "rule_ids": ["MISSING_REQUIRED_FIELD"],
            "reasons": [
                {
                    "rule": "MISSING_REQUIRED_FIELD",
                    "message": "vendor is missing.",
                    "human_review_required": True,
                }
            ],
            "evidence": {
                "invoice_id": "INV005",
                "vendor": None,
                "amount": 4500,
                "category": "Travel",
                "invoice_date": "2026-09-14",
            },
        },
    ]


def test_statistics_and_review_queue():
    results = sample_results()
    stats = get_statistics(results)
    assert stats["total"] == 2
    assert stats["clean"] == 1
    assert stats["exceptions"] == 1
    assert stats["human_review"] == 1

    queue = get_review_queue(results)
    assert queue["count"] == 1
    assert queue["invoices"][0]["invoice_id"] == "INV005"


def test_explain_invoice_is_evidence_grounded():
    result = explain_invoice("INV005", sample_results())
    assert result["ok"] is True
    assert result["status"] == "EXCEPTION"
    assert result["route"] == "HUMAN_REVIEW"
    assert result["findings"][0]["rule"] == "MISSING_REQUIRED_FIELD"
    assert result["evidence"]["vendor"] is None


def test_duplicate_tool_does_not_invent_matches():
    result = find_potential_duplicates("INV005", sample_results())
    assert result["ok"] is True
    assert result["count"] == 0


def test_context_uses_current_invoice():
    context = build_tool_context(
        "Why is this flagged?",
        sample_results(),
        current_invoice_id="INV005",
    )
    assert context["invoice"]["invoice_id"] == "INV005"
    assert context["invoice"]["status"] == "EXCEPTION"
