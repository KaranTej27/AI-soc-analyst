import pandas as pd
import sys
import os

# Add the parent directory to sys.path to import the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.schema_adapter import detect_and_standardize_schema

def test_normalization():
    print("Testing normalization...")
    df = pd.DataFrame([["1.1.1.1", "2023-01-01", 200, "/"]], columns=["  IP_Address  ", "TimeSTAMP  ", "  STATUS  ", "  Path  "])
    df_clean = detect_and_standardize_schema(df)
    expected = {"ip", "timestamp", "status", "endpoint"}
    print(f"Columns: {set(df_clean.columns)}")
    assert set(df_clean.columns) == expected
    print("✓ Normalization passed")

def test_variants():
    print("Testing variants...")
    test_cases = [
        ({"source_ip": ["1.1.1.1"], "datetime": ["2023-01-01"], "response_code": [200], "uri": ["/test"]}, {"ip", "timestamp", "status", "endpoint"}),
        ({"client_ip": ["1.1.1.1"], "event_time": ["2023-01-01"], "status_code": [404], "url": ["/api"]}, {"ip", "timestamp", "status", "endpoint"}),
    ]
    for data, expected_cols in test_cases:
        df = pd.DataFrame(data)
        df_clean = detect_and_standardize_schema(df)
        assert set(df_clean.columns) == expected_cols
    print("✓ Variants passed")

def test_defaults():
    print("Testing defaults...")
    # Only timestamp provided
    df = pd.DataFrame({"timestamp": ["2023-01-01"]})
    df_clean = detect_and_standardize_schema(df)
    assert df_clean.iloc[0]["ip"] == "global"
    assert df_clean.iloc[0]["status"] == 200
    assert df_clean.iloc[0]["endpoint"] == "unknown"
    print("✓ Defaults passed")

def test_missing_timestamp():
    print("Testing missing timestamp...")
    df = pd.DataFrame({"ip": ["1.1.1.1"]})
    try:
        detect_and_standardize_schema(df)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "timestamp" in str(e)
    print("✓ Missing timestamp validation passed")

if __name__ == "__main__":
    test_normalization()
    test_variants()
    test_defaults()
    test_missing_timestamp()
    print("\nAll tests passed successfully!")
