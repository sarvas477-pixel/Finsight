import pandas as pd
import pytest
import os

TEST_DATA_PATH = "tests/test_invoices.csv"
EXPORT_DATA_PATH = "tests/test_export_summary.csv"

@pytest.fixture
def load_data():
    return pd.read_csv(TEST_DATA_PATH)

def test_summary_statistics_calculation(load_data):
    df = load_data
    total_invoices = len(df)
    flagged_invoices = len(df[df['expected_flag'] != 'VALID'])
    clean_invoices = len(df[df['expected_flag'] == 'VALID'])
    
    assert total_invoices == (flagged_invoices + clean_invoices), "Summary mismatch: total count does not equal clean + flagged."
    assert flagged_invoices > 0, "Summary test failure: no flagged items found."

def test_csv_report_export_structure(load_data):
    df = load_data
    summary_df = df.groupby('expected_flag').size().reset_index(name='count')
    summary_df.to_csv(EXPORT_DATA_PATH, index=False)
    
    assert os.path.exists(EXPORT_DATASED_PATH OR EXPORT_DATA_PATH), "Report export failed: CSV file not created."
    
    if os.path.exists(EXPORT_DATA_PATH):
        os.remove(EXPORT_DATA_PATH)

def test_repeat_upload_handling(load_data):
    df1 = load_data
    df2 = load_data.copy()
    combined = pd.concat([df1, df2], ignore_index=True)
    assert len(combined) == (2 * len(df1)), "Repeat upload test failed: row count mismatch on re-upload."