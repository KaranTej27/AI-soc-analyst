import pandas as pd
import sys
import os
import tempfile

# Add the parent directory to sys.path to import the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.preprocessing import build_features

def test_preprocessing_integration():
    print("Testing preprocessing integration with schema adapter...")
    
    # Create a dummy CSV with messy headers and minimal columns
    data = """  source_ip  ,  Time  
1.1.1.1,2023-01-01 10:00:00
1.1.1.1,2023-01-01 10:01:00
2.2.2.2,2023-01-01 10:05:00
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(data)
        temp_path = f.name
        
    try:
        df_features = build_features(temp_path)
        print(f"Features columns: {df_features.columns.tolist()}")
        
        # Check if features were engineered correctly
        assert "ip" in df_features.columns
        assert "window_start" in df_features.columns
        assert "total_requests" in df_features.columns
        
        # Verify default values were used during preprocessing
        # (Though they are internal to build_features, the output should exist)
        assert not df_features.empty
        print("✓ Preprocessing integration passed")
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    try:
        test_preprocessing_integration()
        print("\nIntegration test passed successfully!")
    except Exception as e:
        print(f"\nIntegration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
