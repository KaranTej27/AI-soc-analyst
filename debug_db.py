import os
import sys
from dotenv import load_dotenv
import psycopg2
from passlib.context import CryptContext

# Force load .env from current directory
load_dotenv()

url = os.environ.get("DATABASE_URL")
print(f"Testing connection...")

try:
    # 1. Test Hashing (Critical after sync)
    print("Testing password hashing...")
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_ctx.hash("testpassword")
    print("SUCCESS: Password hashed.")

    # 2. Test DB Connection
    if not url:
        print("FAILED: DATABASE_URL not found in .env")
        sys.exit(1)
        
    conn = psycopg2.connect(url)
    print("SUCCESS: Connected to PostgreSQL!")
    
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    
    # Check if table exists
    cur.execute("SELECT to_regclass('public.users');")
    result = cur.fetchone()
    if result and result[0]:
        print("SUCCESS: 'users' table exists.")
    else:
        print("WARNING: 'users' table does NOT exist. (App should create it on startup)")
        
    conn.close()
    
except Exception as e:
    print("\nFAILED. Error details:")
    print(e)
