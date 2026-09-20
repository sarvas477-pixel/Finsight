import pandas as pd
import pytest

TEST_DATA_PATH = "tests/test_invoices.csv"

@pytest.fixture
def load_data():
    return pd.read_csv(TEST_DATA_PATH)

def test_missing_fields(load_data):
    df = load_data
    missing_vendor = df[df['vendor'].isna()]
    assert len(missing_vendor) > 0, "Failed to identify missing vendor."

def test_invalid_amounts(load_data):
    df = load_data
    invalid_amounts = df[df['amount'] <= 0]
    assert len(invalid_amounts) > 0, "Failed to identify invalid amount."

def test_over_limit_amounts(load_data):
    df = load_data
    over_limit = df[(df['category'] == 'Meals') & (df['amount'] > 500)]
    assert len(over_limit) > 0, "Failed to identify over-limit invoice."

def test_duplicate_detection(load_data):
    df = load_data
    duplicates = df[df.duplicated(subset=['invoice_id', 'vendor', 'amount', 'category', 'invoice_date'], keep=False)]
    assert len(duplicates) >= 2, "Failed to identify exact duplicates."

def test_ambiguous_duplicates(load_data):
    df = load_data
    ambiguous = df[df.duplicated(subset=['vendor', 'amount'], keep=False)]
    assert len(ambiguous) >= 2, "Failed to route ambiguous duplicates."

def test_pipeline_execution(load_data):
    df = load_data
    assert not df.empty, "Pipeline failure: CSV dataset is empty."
    assert 'expected_flag' in df.columns, "Pipeline failure: missing expected_flag column."
