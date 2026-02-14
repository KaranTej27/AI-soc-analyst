import pandas as pd
import os
import sys

# Add app directory to path
sys.path.append(os.getcwd())

from app.services.preprocessing import build_features
from app.services.model import run_isolation_forest
from app.services.risk import assign_risk_levels

def test_pipeline(name, data, expected_error=None):
    print(f"\n--- Testing: {name} ---")
    file_path = f"temp_test_{name}.csv"
    pd.DataFrame(data).to_csv(file_path, index=False)
    
    try:
        df = build_features(file_path)
        df = run_isolation_forest(df)
        df = assign_risk_levels(df)
        print("Success: Pipeline completed.")
        print(f"Result shape: {df.shape}")
        if expected_error:
            print(f"FAIL: Expected error '{expected_error}' but pipeline succeeded.")
    except Exception as e:
        print(f"Caught expected error: {str(e)}" if expected_error and expected_error in str(e) else f"Error: {str(e)}")
        if expected_error and expected_error not in str(e):
             print(f"FAIL: Expected error containing '{expected_error}'")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# 1. Test standard variants (requested by user)
test_pipeline("variants", {
    "IP": ["192.168.1.1", "192.168.1.2"],
    "Time": ["2026-02-14 10:00:00", "2026-02-14 10:01:00"],
    "URL": ["/index", "/login"],
    "Staus": [200, 404]
})

# 2. Test bad timestamps
test_pipeline("bad_times", {
    "ip": ["1.1.1.1", "1.1.1.1"],
    "timestamp": ["invalid", "corrupt"],
    "endpoint": ["/a", "/b"],
    "status": [200, 200]
}, expected_error="Timestamp parsing failed")

# 3. Test empty data
test_pipeline("empty", {
    "ip": [],
    "timestamp": [],
    "endpoint": [],
    "status": []
}, expected_error="The uploaded CSV file is empty")

# 4. Test missing columns
test_pipeline("missing_cols", {
    "something": [1, 2],
    "else": [3, 4]
}, expected_error="Dataset missing required columns")

# 5. Test single row (robustness check)
test_pipeline("single_row", {
    "ip": ["1.1.1.1"],
    "timestamp": ["2026-02-14 10:00:00"],
    "endpoint": ["/home"],
    "status": [200]
})
