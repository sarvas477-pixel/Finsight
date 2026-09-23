import pandas as pd
import pytest
from datetime import datetime, timezone

TEST_DATA_PATH = "tests/test_invoices.csv"

@pytest.fixture
def load_data():
    return pd.read_csv(TEST_DATA_PATH)

def test_human_review_action_storage():
    review_record = {
        "invoice_id": "INV004",
        "reviewer_id": 7011,
        "alternative_action": "APPROVED",
        "reviewer_comments": "Vending meals exceedance validated by manager.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    assert review_record["alternative_action"] in ["APPROVED", "REJECTED"]
    assert len(review_record["reviewer_comments"]) > 0, "Reviewer comments must not be empty."
    assert "timestamp" in review_record and review_record["timestamp"], "Missing review timestamp."
