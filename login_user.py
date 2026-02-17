import os
import psycopg2
import bcrypt
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Establish a safe database connection."""
    try:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is not set.")
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"CRITICAL: Failed to connect to database. {e}")
        return None

def verify_user_login(identifier, password):
    """
    Strict authentication check.
    Succeeds only if:
    1. identifier (username or email) exists
    2. password matches the stored bcrypt hash
    """
    if not identifier or not password:
        return False, "Input fields cannot be empty."

    conn = get_db_connection()
    if not conn:
        return False, "Infrastructure Error: Database unavailable."

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Secure parameterized query to prevent SQL Injection
            # Checks both username and email
            query = """
                SELECT username, email, password_hash 
                FROM ai_soc_analyst_credentials 
                WHERE username = %s OR email = %s;
            """
            cur.execute(query, (identifier, identifier))
            user = cur.fetchone()

            if not user:
                return False, "Login failed: User not found."

            # Verify password using bcrypt (Safe comparison)
            stored_hash = user['password_hash']
            
            # handle cases where stored_hash might be string from DB
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
            
            if isinstance(password, str):
                password = password.encode('utf-8')

            if bcrypt.checkpw(password, stored_hash):
                return True, f"SUCCESS: Welcome back, {user['username']}!"
            else:
                return False, "Login failed: Incorrect password."

    except Exception as e:
        return False, f"Unexpected error during login: {str(e)}"
    finally:
        if conn:
            conn.close()

def main():
    """Interactive login test for production verification."""
    print("\n--- AI SOC Analyst Secure Login ---")
    
    # In a real CLI app, we might use getpass for password input
    identifier = input("Username or Email: ").strip()
    password = input("Password: ").strip()

    success, message = verify_user_login(identifier, password)

    if success:
        print(f"\n[+] {message}")
        sys.exit(0) # Success exit code
    else:
        print(f"\n[-] {message}")
        sys.exit(1) # Error exit code

if __name__ == "__main__":
    main()
