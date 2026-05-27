"""
SQLite-based API key management for the Cloudflare LLM Proxy.
Stores proxy API keys that users must present to access the OpenAI-compatible endpoints.
"""

import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "proxy_keys.db"


def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the database and create the keys table if it doesn't exist."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL DEFAULT 'default',
                created_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)
        conn.commit()
    finally:
        conn.close()


def generate_api_key(name: str = "default") -> dict:
    """
    Generate a new API key with the given name.
    Returns a dict with the key details.
    """
    key = f"cfpk_{secrets.token_hex(24)}"
    created_at = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO api_keys (key, name, created_at, is_active) VALUES (?, ?, ?, 1)",
            (key, name, created_at),
        )
        conn.commit()
        return {
            "id": cursor.lastrowid,
            "key": key,
            "name": name,
            "created_at": created_at,
            "is_active": True,
        }
    finally:
        conn.close()


def validate_api_key(key: str) -> Optional[dict]:
    """
    Validate an API key. Returns the key record if valid and active, None otherwise.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM api_keys WHERE key = ? AND is_active = 1", (key,)
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def list_api_keys() -> list[dict]:
    """List all API keys (without exposing the full key values for security)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, created_at, is_active FROM api_keys ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def revoke_api_key(key_id: int) -> bool:
    """Revoke (deactivate) an API key by its ID. Returns True if successful."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
