from typing import Any, Dict


def prepare_ai_input(
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convert deterministic M1 rule-engine output
    into a stable structure for M2.

    M1 owns the facts and decision.

    M2 may explain these facts but must not
    change the decision.
    """

    return {
        "invoice_id": result.get(
            "invoice_id"
        ),

        "status": result.get(
            "status"
        ),

        "human_review_required": result.get(
            "human_review_required",
            False
        ),

        "rule_ids": result.get(
            "rule_ids",
            []
        ),

        "reasons": result.get(
            "reasons",
            []
        ),

        "evidence": result.get(
            "evidence",
            {}
        ),
    }


def prepare_batch_ai_input(results):
    """
    Prepare multiple M1 results for M2.
    """

    return [
        prepare_ai_input(result)
        for result in results
    ]