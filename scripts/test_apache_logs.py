import pandas as pd
import os
import sys

# Add app directory to path
sys.path.append(os.getcwd())

from app.services.preprocessing import build_features

def test_apache_timestamps():
    print("\n--- Testing: Apache/Nginx Timestamps ---")
    data = {
        "ip": ["10.0.0.1", "10.0.0.2"],
        "timestamp": ["10/Oct/2000:13:55:36 -0700", "[10/Oct/2000:13:55:36 -0700]"],
        "endpoint": ["/index", "/api"],
        "status": [200, 404]
    }
    
    file_path = "temp_apache_test.csv"
    pd.DataFrame(data).to_csv(file_path, index=False)
    
    try:
        df = build_features(file_path)
        print("Success: Apache timestamps parsed correctly.")
        print(df[["ip", "window_start", "total_requests"]])
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    test_apache_timestamps()
