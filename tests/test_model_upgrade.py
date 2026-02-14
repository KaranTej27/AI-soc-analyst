import pandas as pd
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.model import run_isolation_forest

def test_small_dataset_zscore():
    print("Testing small dataset (Z-score logic)...")
    # 10 rows < 50
    data = {
        "feat1": np.random.normal(0, 1, 10).tolist(),
        "feat2": np.random.normal(0, 1, 10).tolist(),
        "text_col": ["a"] * 10
    }
    # Add one obvious outlier
    data["feat1"][0] = 100 
    
    df = pd.DataFrame(data)
    result = run_isolation_forest(df)
    
    assert "anomaly_label" in result.columns
    assert "anomaly_score" in result.columns
    assert "risk_score" in result.columns
    assert result.iloc[0]["anomaly_label"] == -1
    assert 0 <= result.iloc[0]["risk_score"] <= 100
    print("✓ Small dataset passed")

def test_large_dataset_iforest():
    print("Testing large dataset (Isolation Forest logic)...")
    # 60 rows >= 50
    n = 60
    data = {
        "feat1": np.random.normal(0, 1, n).tolist(),
        "feat2": np.random.normal(0, 1, n).tolist()
    }
    # Add one obvious outlier
    data["feat1"][0] = 100
    
    df = pd.DataFrame(data)
    result = run_isolation_forest(df)
    
    assert result.iloc[0]["anomaly_label"] == -1
    assert 0 <= result.iloc[0]["risk_score"] <= 100
    print("✓ Large dataset passed")

def test_mixed_types_and_nans():
    print("Testing mixed types and NaNs...")
    data = {
        "feat1": [1.0, 2.0, np.nan, 4.0, 100.0],
        "feat2": [10.0, 11.0, 12.0, np.nan, 200.0],
        "category": ["A", "B", "C", "D", "E"]
    }
    df = pd.DataFrame(data)
    # Should not crash and should work on numeric columns
    result = run_isolation_forest(df)
    assert not result["risk_score"].isna().any()
    print("✓ Mixed types and NaNs passed")

def test_empty_numeric():
    print("Testing with no numeric columns...")
    df = pd.DataFrame({"col1": ["a", "b", "c"]})
    result = run_isolation_forest(df)
    assert "risk_score" in result.columns
    assert (result["risk_score"] == 0).all()
    print("✓ Empty numeric passed")

if __name__ == "__main__":
    try:
        test_small_dataset_zscore()
        test_large_dataset_iforest()
        test_mixed_types_and_nans()
        test_empty_numeric()
        print("\nAll model upgrade tests passed successfully!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
