import sys
import os
import io
from fastapi.testclient import TestClient

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

client = TestClient(app)

def test_reject_non_csv():
    print("Testing non-CSV rejection...")
    file_content = b"This is not a CSV"
    response = client.post(
        "/upload",
        files={"file": ("test.txt", file_content, "text/plain")}
    )
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
    assert response.status_code == 400
    assert "Invalid file type" in response.text
    print("✓ Non-CSV rejection passed")

def test_api_json_error():
    print("Testing JSON error response for API mode...")
    file_content = b"This is not a CSV"
    response = client.post(
        "/upload",
        files={"file": ("test.txt", file_content, "text/plain")},
        headers={"Accept": "application/json"}
    )
    assert response.status_code == 400
    assert response.json()["status"] == "error"
    print("✓ JSON error response passed")

def test_successful_upload_json():
    print("Testing successful upload with JSON response...")
    csv_content = "ip,timestamp\n1.1.1.1,2023-01-01 10:00:00"
    response = client.post(
        "/upload",
        files={"file": ("test.csv", csv_content, "text/csv")},
        headers={"Accept": "application/json"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "metrics" in data
    assert "rows_processed" in data["metrics"]
    print("✓ Successful JSON upload passed")

def test_successful_upload_redirect():
    print("Testing successful upload with redirect (UI mode)...")
    csv_content = "ip,timestamp\n1.1.1.1,2023-01-01 10:00:00"
    response = client.post(
        "/upload",
        files={"file": ("test.csv", csv_content, "text/csv")},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/logs"
    print("✓ UI redirect passed")

if __name__ == "__main__":
    try:
        test_reject_non_csv()
        test_api_json_error()
        test_successful_upload_json()
        test_successful_upload_redirect()
        print("\nAll upload hardening tests passed successfully!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
