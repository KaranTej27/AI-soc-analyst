from app.database.db import DatabaseManager
import time

def run_verification():
    print("--- Starting Credential System Verification ---")

    # 1. Create a Test User
    username = "test_analyst"
    email = "analyst@example.com"
    password = "SecurePassword123!"
    
    print(f"\n[1] Creating user '{username}'...")
    user_id = DatabaseManager.create_user(username, email, password)
    
    if user_id:
        print(f"SUCCESS: User created with ID: {user_id}")
    else:
        print("FAILED: Could not create user (might already exist).")
        # Attempt to fetch existing to continue test
        user = DatabaseManager.get_user_by_username(username)
        if user:
            print("User already exists, continuing test...")
        else:
            return

    # 2. Verify Login
    print(f"\n[2] Verifying login for '{username}'...")
    if DatabaseManager.verify_login(username, password):
        print("SUCCESS: Login verified.")
    else:
        print("FAILED: Login verification failed.")

    if not DatabaseManager.verify_login(username, "WrongPassword"):
        print("SUCCESS: Rejected incorrect password.")
    else:
        print("FAILED: Accepted incorrect password!")

    # 3. Test Dynamic Updates (Email)
    print(f"\n[3] Updating email for '{username}'...")
    new_email = "new_analyst@example.com"
    
    # Get original updated_at
    user_before = DatabaseManager.get_user_by_username(username)
    print(f"Original updated_at: {user_before['updated_at']}")
    
    time.sleep(1) # Ensure timestamp difference
    
    if DatabaseManager.update_email(username, new_email):
        print("SUCCESS: Email update trigger fired.")
        user_after = DatabaseManager.get_user_by_username(username)
        print(f"New updated_at:      {user_after['updated_at']}")
        
        if user_after['updated_at'] > user_before['updated_at']:
             print("SUCCESS: 'updated_at' timestamp was automatically updated!")
        else:
             print("FAILED: Timestamp did not change.")
    else:
        print("FAILED: Could not update email.")

    # 4. Test Password Update
    print(f"\n[4] Updating password for '{username}'...")
    new_password = "NewSecurePassword456!"
    if DatabaseManager.update_password(username, new_password):
        print("SUCCESS: Password updated.")
        if DatabaseManager.verify_login(username, new_password):
             print("SUCCESS: New password verified.")
        else:
             print("FAILED: New password verification failed.")
    else:
        print("FAILED: Password update failed.")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    try:
        run_verification()
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Ensure the database 'AI SOC Analyst Credentials' exists and DATABASE_URL is correct.")
