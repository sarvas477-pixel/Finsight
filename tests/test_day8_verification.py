import pandas as pd
import pytest

TEST_DATA_PATH = "tests/test_invoices.csv"

@pytest.fixture
def load_data():
    return pd.read_csv(TEST_DATA_PATH)

def test_verify_flags_against_spreadsheet(load_data):
    df = load_data
    
    # Verify required fields (missing vendor)
    missing_vendor_rows = df[df['vendor'].isna()]
    for idx, row in missing_vendor_rows.iterrows():
        assert row['expected_flag'] == 'MISSING_VENDOR', f"Mismatch on row {idx}: expected MISSING_VENDOR"

    # Verify invalid amounts
    invalid_amount_rows = df[df['amount'] <= 0]
    for idx, row in invalid_amount_rows.iterrows():
        assert row['expected_flag'] == 'INVALID_AMOUNT', f"Mismatch on row {idx}: expected INVALID_AMOUNT"

    # Verify over-limit amounts
    over_limit_rows = df[(df['category'] == 'Meals') & (df['amount'] > 500)]
    for idx, row in over_limit_rows.iterrows():
        assert row['expected_flag'] == 'OVER_LIMIT', f"Mismatch on row {idx}: expected OVER_LIMIT"

    # Verify exact duplicates
    duplicate_rows = df[df.duplicated(subset=['invoice_id', 'vendor', 'amount', 'category', 'invoice_date'], keep=False)]
    for idx, row in duplicate_rows.iterrows():
        assert row['expected_flag'] == 'DUPLICATE', f"Mismatch on row {idx}: expected DUPLICATE"
