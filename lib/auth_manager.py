"""
Authentication Management Library for Packing Website

This is the CORE authentication library that handles:
- Database schema and initialization
- Password generation, hashing, and verification
- Session management (tokens)
- Audit logging

IMPORTANT: Do not use this module directly for admin tasks. Instead, use the 
CLI tool: tools/manage_auth.py

Examples:
    # Using the convenience script (runs inside Docker):
    ./tools/auth init
    ./tools/auth create 1

The database is stored at the location specified by SQLITE_DB_PATH environment
variable, or defaults to: /zpool/dev/PackingWebsite/db/packingwebsite.db
"""

import sqlite3
import bcrypt
import secrets
import json
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional, Dict, List
import subprocess
import sys
from pathlib import Path

# Verify xkcdpass is available at import time
try:
    subprocess.run(['xkcdpass', '--help'], capture_output=True, check=True)
except (subprocess.CalledProcessError, FileNotFoundError):
    print("\n" + "!" * 60, file=sys.stderr)
    print("FATAL: xkcdpass is NOT installed!", file=sys.stderr)
    print("!" * 60, file=sys.stderr)
    print("Install it immediately:", file=sys.stderr)
    print("    pip install xkcdpass", file=sys.stderr)
    print("!" * 60 + "\n", file=sys.stderr)
    sys.exit(1)

# Database management
def get_db_path():
    """Get the database path from the environment variable or use the default."""
    default_path = str(Path(__file__).resolve().parent.parent / 'db' / 'packingwebsite.db')
    return os.environ.get('SQLITE_DB_PATH', default_path)

@contextmanager
def get_db():
    """Get a database connection with automatic cleanup"""
    db_path = get_db_path()
    
    # Ensure the directory exists
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with required tables"""
    with get_db() as db:
        # Stores table - one password per store
        db.execute('''
            CREATE TABLE IF NOT EXISTS store_auth (
                store_id TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Sessions table - for web authentication
        db.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                store_id TEXT NOT NULL,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES store_auth(store_id)
            )
        ''')
        
        # Audit log for tracking access
        db.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
        ''')
        
        db.commit()

def generate_passphrase(words: int = 3) -> str:
    """
    Generate an XKCD-936 style passphrase using xkcdpass
    
    Args:
        words: Number of words in the passphrase (default: 3)
    
    Returns:
        A passphrase like "happy-tiger-blue"
    
    Raises:
        RuntimeError: If xkcdpass is not installed
    """
    try:
        # Use eff-special wordlist for more common, memorable words
        result = subprocess.run(
            ['xkcdpass', '-w', 'eff-special', '-n', str(words), '-d', '-'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # ABSOLUTELY NO FALLBACK - xkcdpass is REQUIRED!
        raise RuntimeError(
            "\n" + "=" * 60 + "\n"
            "CRITICAL ERROR: xkcdpass IS NOT INSTALLED!\n"
            "=" * 60 + "\n"
            "This application REQUIRES xkcdpass for secure password generation.\n"
            "There is NO fallback and NO excuse for not having it installed.\n\n"
            "Install it NOW:\n"
            "    pip install xkcdpass\n"
            "    OR\n"
            "    docker compose exec web pip install xkcdpass\n\n"
            "DO NOT attempt to use this authentication system without xkcdpass!\n"
            "We rely on the EFF wordlists for cryptographically sound passphrases.\n"
            "=" * 60
        )

def normalize_password(password: str) -> str:
    """
    Normalize a password for consistent comparison
    - Convert to lowercase
    - Keep only a-z characters
    
    This allows users to enter passwords in various formats:
    "Happy-Tiger-Blue", "happy tiger blue", "HAPPY TIGER BLUE" all become "happytigerblue"
    
    Args:
        password: The raw password input
    
    Returns:
        Normalized password containing only lowercase a-z
    """
    # Convert to lowercase and keep only a-z characters
    return ''.join(c for c in password.lower() if 'a' <= c <= 'z')

def create_store_auth(store_id: str, password: Optional[str] = None) -> str:
    """
    Create or update authentication for a store
    
    Args:
        store_id: The store identifier (e.g., "1", "2", etc.)
        password: Optional password. If not provided, generates one
    
    Returns:
        The password (either provided or generated)
    """
    if password is None:
        password = generate_passphrase()
    
    # Normalize the password before hashing
    normalized = normalize_password(password)
    password_hash = bcrypt.hashpw(normalized.encode('utf-8'), bcrypt.gensalt())
    
    with get_db() as db:
        # Check if store already has auth
        existing = db.execute(
            "SELECT * FROM store_auth WHERE store_id = ?", 
            (store_id,)
        ).fetchone()
        
        if existing:
            # Update existing
            db.execute(
                """UPDATE store_auth 
                   SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE store_id = ?""",
                (password_hash, store_id)
            )
            action = "password_updated"
        else:
            # Create new
            db.execute(
                "INSERT INTO store_auth (store_id, password_hash) VALUES (?, ?)",
                (store_id, password_hash)
            )
            action = "store_created"
        
        # Log the action
        db.execute(
            "INSERT INTO audit_log (store_id, action) VALUES (?, ?)",
            (store_id, action)
        )
        
        db.commit()
    
    return password

def verify_store_password(store_id: str, password: str) -> bool:
    """
    Verify a password for a store
    
    Args:
        store_id: The store identifier
        password: The password to verify
    
    Returns:
        True if password is correct, False otherwise
    """
    with get_db() as db:
        result = db.execute(
            "SELECT password_hash FROM store_auth WHERE store_id = ?",
            (store_id,)
        ).fetchone()
        
        if not result:
            return False
        
        # Normalize the password before checking
        normalized = normalize_password(password)
        is_valid = bcrypt.checkpw(
            normalized.encode('utf-8'), 
            result['password_hash']
        )
        
        # Log the attempt
        db.execute(
            "INSERT INTO audit_log (store_id, action, details) VALUES (?, ?, ?)",
            (store_id, "login_attempt", json.dumps({"success": is_valid}))
        )
        db.commit()
        
        return is_valid

def create_session(store_id: str, hours: int = 24) -> str:
    """
    Create a new session token for a store
    
    Args:
        store_id: The store identifier
        hours: How many hours the session should last
    
    Returns:
        The session token
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=hours)
    
    with get_db() as db:
        # Clean up old sessions first
        db.execute(
            "DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP"
        )
        
        # Create new session
        db.execute(
            "INSERT INTO sessions (token, store_id, expires_at) VALUES (?, ?, ?)",
            (token, store_id, expires_at)
        )
        
        # Log the session creation
        db.execute(
            "INSERT INTO audit_log (store_id, action) VALUES (?, ?)",
            (store_id, "session_created")
        )
        
        db.commit()
    
    return token

def verify_session(token: str) -> Optional[str]:
    """
    Verify a session token and return the store_id if valid
    
    Args:
        token: The session token to verify
    
    Returns:
        The store_id if valid, None otherwise
    """
    with get_db() as db:
        result = db.execute(
            """SELECT store_id FROM sessions 
               WHERE token = ? AND expires_at > CURRENT_TIMESTAMP""",
            (token,)
        ).fetchone()
        
        if result:
            return result['store_id']
        
        return None

def delete_session(token: str):
    """Delete a session (logout)"""
    with get_db() as db:
        # Get store_id for logging
        result = db.execute(
            "SELECT store_id FROM sessions WHERE token = ?",
            (token,)
        ).fetchone()
        
        if result:
            store_id = result['store_id']
            
            # Delete the session
            db.execute("DELETE FROM sessions WHERE token = ?", (token,))
            
            # Log the logout
            db.execute(
                "INSERT INTO audit_log (store_id, action) VALUES (?, ?)",
                (store_id, "logout")
            )
            
            db.commit()

def list_stores() -> List[Dict]:
    """List all stores with auth configured"""
    with get_db() as db:
        results = db.execute(
            """SELECT store_id, created_at, updated_at 
               FROM store_auth 
               ORDER BY store_id"""
        ).fetchall()
        
        return [dict(row) for row in results]

def hasAuth(store_id: str) -> bool:
    """Check if a store has authentication configured"""
    with get_db() as db:
        result = db.execute(
            "SELECT 1 FROM store_auth WHERE store_id = ?",
            (store_id,)
        ).fetchone()
        
        return result is not None

def get_audit_log(store_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """
    Get audit log entries
    
    Args:
        store_id: Optional filter by store
        limit: Maximum number of entries to return
    
    Returns:
        List of audit log entries
    """
    with get_db() as db:
        if store_id:
            query = """SELECT * FROM audit_log 
                      WHERE store_id = ? 
                      ORDER BY timestamp DESC 
                      LIMIT ?"""
            results = db.execute(query, (store_id, limit)).fetchall()
        else:
            query = """SELECT * FROM audit_log 
                      ORDER BY timestamp DESC 
                      LIMIT ?"""
            results = db.execute(query, (limit,)).fetchall()
        
        return [dict(row) for row in results]

# This module is a library and should not be executed directly.
# Use tools/manage_auth.py instead for CLI operations.