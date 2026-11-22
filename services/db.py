"""
Database service for Civicsaathi.
Provides lightweight, reliable SQLite persistence for user preferences such as selected language.
"""

import sqlite3
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "civicsaathi.db"


def get_db_path() -> Path:
    """Ensure data directory exists and return database file path."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_DB_PATH


def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize database tables."""
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language_code TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()


def get_user_language(user_id: int, db_path: Optional[Path] = None) -> Optional[str]:
    """Retrieve saved language code for a user, or None if not set."""
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT language_code FROM users WHERE user_id = ?;",
            (user_id,),
        )
        row = cursor.fetchone()
        return row[0] if row else None


def set_user_language(user_id: int, language_code: str, db_path: Optional[Path] = None) -> None:
    """Store or update user's language preference."""
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (user_id, language_code, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                language_code = excluded.language_code,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (user_id, language_code),
        )
        conn.commit()


def delete_user_language(user_id: int, db_path: Optional[Path] = None) -> None:
    """Delete language record for testing or account reset."""
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?;", (user_id,))
        conn.commit()
