import os
import psycopg2
from psycopg2.extras import RealDictCursor
from passlib.context import CryptContext
from contextlib import contextmanager
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Make sure DATABASE_URL is set in your environment
# If not set, it defaults to a local connection string (adjust as needed)
DATABASE_URL = os.getenv("DATABASE_URL")

# Password Hashing Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Ensures connections are closed properly.
    """
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

class DatabaseManager:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate a bcrypt hash for a password."""
        return pwd_context.hash(password)

    @staticmethod
    def create_user(username: str, email: str, password: str) -> Optional[int]:
        """
        Create a new user with a hashed password.
        Returns the new user's ID on success, None on failure.
        """
        hashed_password = DatabaseManager.get_password_hash(password)
        
        query = """
            INSERT INTO ai_soc_analyst_credentials (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id;
        """
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (username, email, hashed_password))
                    user_id = cur.fetchone()[0]
                    conn.commit()
                    return user_id
        except Exception as e:
            if "unique constraint" in str(e).lower():
                print(f"Error: Username '{username}' or Email '{email}' already exists.")
            else:
                print(f"Error creating user: {e}")
            return None

    @staticmethod
    def get_user_by_identifier(identifier: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by username or email.
        """
        query = "SELECT * FROM ai_soc_analyst_credentials WHERE username = %s OR email = %s;"
        
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (identifier, identifier))
                    return cur.fetchone()
        except Exception as e:
            print(f"Error fetching user by identifier: {e}")
            return None

    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by username.
        """
        return DatabaseManager.get_user_by_identifier(username)

    @staticmethod
    def verify_login(username: str, password: str) -> bool:
        """
        Check if a username and password match.
        """
        user = DatabaseManager.get_user_by_username(username)
        if not user:
            return False
        return DatabaseManager.verify_password(password, user['password_hash'])

    @staticmethod
    def update_email(username: str, new_email: str) -> bool:
        """
        Update a user's email address.
        Triggers 'updated_at' auto-update in DB.
        """
        query = "UPDATE ai_soc_analyst_credentials SET email = %s WHERE username = %s;"
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (new_email, username))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            if "unique constraint" in str(e).lower():
                print(f"Error: Email '{new_email}' is already in use.")
            else:
                print(f"Error updating email: {e}")
            return False

    @staticmethod
    def update_password(username: str, new_password: str) -> bool:
        """
        Update a user's password securely.
        """
        new_hash = DatabaseManager.get_password_hash(new_password)
        query = "UPDATE ai_soc_analyst_credentials SET password_hash = %s WHERE username = %s;"
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (new_hash, username))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            print(f"Error updating password: {e}")
            return False
