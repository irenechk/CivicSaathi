"""
SQLite database connection and schema management for Civicsaathi.
Designed to be lightweight for development and structured for clean migration to PostgreSQL.
"""

import sqlite3
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "civicsaathi.db"


def get_db_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DB_PATH


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_database(db_path: Optional[Path] = None) -> None:
    """Initialize all core tables in SQLite."""
    conn = get_connection(db_path)
    with conn:
        cursor = conn.cursor()

        # 1. Telegram user preferences
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language_code TEXT NOT NULL DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 2. Canonical Scheme Records
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schemes (
                scheme_id TEXT PRIMARY KEY,
                scheme_name TEXT NOT NULL,
                alternate_names_json TEXT,
                scheme_level TEXT NOT NULL DEFAULT 'central',
                state_or_ut TEXT NOT NULL DEFAULT 'all',
                districts_json TEXT,
                ministry TEXT,
                department TEXT,
                description TEXT NOT NULL,
                objective TEXT,
                target_beneficiaries_json TEXT,
                benefit_type_json TEXT,
                benefit_amount TEXT,
                benefit_frequency TEXT,
                eligibility_json TEXT,
                exclusion_conditions_json TEXT,
                required_documents_json TEXT,
                application_process_json TEXT,
                application_mode TEXT,
                official_application_url TEXT,
                official_scheme_url TEXT,
                official_source_urls_json TEXT,
                guidelines_document_urls_json TEXT,
                application_status TEXT NOT NULL,
                launch_date TEXT,
                last_updated_date TEXT,
                research_verified_date TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                source_notes_json TEXT,
                data_gaps_json TEXT,
                research_confidence TEXT NOT NULL,
                raw_payload TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 3. Source Registry
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS source_registry (
                source_ref TEXT PRIMARY KEY,
                publisher TEXT NOT NULL,
                document_or_page_title TEXT NOT NULL,
                exact_url TEXT NOT NULL UNIQUE,
                publication_or_updated_date TEXT,
                access_date TEXT,
                relevant_section TEXT,
                fields_supported TEXT,
                is_approved INTEGER DEFAULT 1,
                last_crawled_at TIMESTAMP,
                crawl_status TEXT DEFAULT 'pending',
                notes TEXT
            );
            """
        )

        # 4. Crawled and Processed Documents
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS crawled_documents (
                doc_id TEXT PRIMARY KEY,
                source_ref TEXT,
                url TEXT NOT NULL,
                doc_type TEXT NOT NULL, -- html, pdf, jsonl
                title TEXT,
                raw_content TEXT,
                cleaned_text TEXT,
                content_hash TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_ref) REFERENCES source_registry (source_ref)
            );
            """
        )

        # 5. Citizen Profiles (with user consent)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS citizen_profiles (
                profile_id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE,
                full_name TEXT,
                language TEXT DEFAULT 'en',
                state TEXT,
                district TEXT,
                age INTEGER,
                gender TEXT,
                occupation TEXT,
                annual_family_income REAL,
                category TEXT,
                education_level TEXT,
                is_disabled INTEGER,
                has_bpl_card INTEGER,
                owns_cultivable_land INTEGER,
                consent_given INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Migration: ensure full_name exists in pre-existing SQLite database
        try:
            cursor.execute("ALTER TABLE citizen_profiles ADD COLUMN full_name TEXT;")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # 6. Scheme Audit and Ingestion Logs
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ingestion_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_name TEXT NOT NULL,
                records_imported INTEGER DEFAULT 0,
                records_skipped INTEGER DEFAULT 0,
                errors_json TEXT,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 7. Multi-Turn Conversation Context & Memory
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_contexts (
                user_id TEXT PRIMARY KEY,
                active_scheme_id TEXT,
                active_scheme_name TEXT,
                history_json TEXT DEFAULT '[]',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 8. Scheme Versioning & Historical Archive
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scheme_versions (
                version_id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheme_id TEXT NOT NULL,
                version_tag TEXT NOT NULL,
                previous_eligibility_json TEXT,
                current_eligibility_json TEXT,
                previous_benefits_json TEXT,
                current_benefits_json TEXT,
                source_document TEXT,
                change_notes TEXT,
                verification_status TEXT,
                created_by TEXT DEFAULT 'system',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scheme_id) REFERENCES schemes (scheme_id)
            );
            """
        )

        # 9. Admin Review Flags & Scraper Alerts
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_review_flags (
                flag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheme_id TEXT NOT NULL,
                flag_type TEXT NOT NULL, -- outdated, conflicting, source_gap, scraper_error
                reason TEXT NOT NULL,
                details_json TEXT,
                status TEXT DEFAULT 'pending', -- pending, resolved, dismissed
                flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                resolved_by TEXT,
                FOREIGN KEY (scheme_id) REFERENCES schemes (scheme_id)
            );
            """
        )

        # 10. Citizen Document Checklist Tracker
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS citizen_documents (
                user_id TEXT NOT NULL,
                document_name TEXT NOT NULL,
                is_available INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, document_name)
            );
            """
        )

        # 11. Citizen Saved Schemes (Bookmarks)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS citizen_saved_schemes (
                user_id TEXT NOT NULL,
                scheme_id TEXT NOT NULL,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, scheme_id),
                FOREIGN KEY (scheme_id) REFERENCES schemes (scheme_id)
            );
            """
        )

        # 12. Citizen Scheme View History
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS citizen_view_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                scheme_id TEXT NOT NULL,
                viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scheme_id) REFERENCES schemes (scheme_id)
            );
            """
        )

        # Indices for rapid lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schemes_level ON schemes (scheme_level);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schemes_state ON schemes (state_or_ut);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schemes_verification ON schemes (verification_status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schemes_ministry ON schemes (ministry);")
    conn.close()
