import pandas as pd
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.risk import assign_risk_levels

def test_risk_formula_full():
    print("Testing hybrid risk formula with all inputs...")
    data = {
        "risk_score": [80.0, 20.0], # Anomaly base
        "success_ratio": [0.5, 1.0], # Failure logic
        "request_rate_per_minute": [10.0, 1.0], # Spike logic
        "window_start": ["2023-01-01 23:00:00", "2023-01-01 12:00:00"] # Time logic
    }
    df = pd.DataFrame(data)
    result = assign_risk_levels(df)
    
    # Row 0 should be HIGH (High anomaly, 50% failure, spike, after-hours)
    assert result.iloc[0]["risk_level"] == "HIGH"
    # Row 1 should be LOW
    assert result.iloc[1]["risk_level"] == "LOW"
    print("✓ Hybrid formula passed")

def test_risk_fallbacks():
    print("Testing risk fallbacks for missing columns...")
    # Only anomaly score exists
    df = pd.DataFrame({"risk_score": [90.0, 10.0]})
    result = assign_risk_levels(df)
    
    assert result.iloc[0]["risk_level"] == "HIGH"
    assert result.iloc[1]["risk_level"] == "LOW"
    assert "risk_level" in result.columns
    print("✓ Fallbacks passed")

def test_risk_sorting():
    print("Testing risk sorting...")
    df = pd.DataFrame({"risk_score": [10.0, 90.0, 50.0]})
    result = assign_risk_levels(df)
    
    assert result.iloc[0]["risk_score"] >= result.iloc[1]["risk_score"]
    assert result.iloc[1]["risk_score"] >= result.iloc[2]["risk_score"]
    print("✓ Sorting passed")

if __name__ == "__main__":
    try:
        test_risk_formula_full()
        test_risk_fallbacks()
        test_risk_sorting()
        print("\nAll risk upgrade tests passed successfully!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
