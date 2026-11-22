"""
Data Ingestion Pipeline for Civicsaathi.
Imports and validates:
- data/raw/schemes_master.jsonl (30 Central Government schemes)
- data/raw/sources_registry.csv (25 official primary sources)
Validates all records using SchemeValidator before persisting to SQLite.
"""

import csv
import json
import sys
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.models import SchemeRecord
from database.connection import get_connection, init_database
from database.repository import SchemeRepository
from scraper.validator import SchemeValidator

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
SCHEMES_JSONL = RAW_DIR / "schemes_master.jsonl"
SOURCES_CSV = RAW_DIR / "sources_registry.csv"


def ingest_sources() -> int:
    if not SOURCES_CSV.exists():
        print(f"Sources file not found at {SOURCES_CSV}")
        return 0

    conn = get_connection()
    count = 0
    with open(SOURCES_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        with conn:
            cursor = conn.cursor()
            for row in reader:
                cursor.execute(
                    """
                    INSERT INTO source_registry (
                        source_ref, publisher, document_or_page_title, exact_url,
                        publication_or_updated_date, access_date, relevant_section, fields_supported
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(exact_url) DO UPDATE SET
                        publisher = excluded.publisher,
                        document_or_page_title = excluded.document_or_page_title,
                        access_date = excluded.access_date,
                        relevant_section = excluded.relevant_section,
                        fields_supported = excluded.fields_supported;
                    """,
                    (
                        row["source_ref"],
                        row["publisher"],
                        row["document_or_page_title"],
                        row["exact_url"],
                        row.get("publication_or_updated_date"),
                        row.get("access_date"),
                        row.get("relevant_section"),
                        row.get("fields_supported"),
                    ),
                )
                count += 1
    conn.close()
    print(f"✅ Ingested {count} official source references into source_registry.")
    return count


def ingest_schemes() -> Dict[str, Any]:
    if not SCHEMES_JSONL.exists():
        print(f"Schemes JSONL file not found at {SCHEMES_JSONL}")
        return {"imported": 0, "errors": 0}

    repo = SchemeRepository()
    valid_count = 0
    error_count = 0
    errors = []

    with open(SCHEMES_JSONL, mode="r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
                is_valid, validation_errors, scheme_record = SchemeValidator.validate_record(data)
                if not is_valid:
                    error_count += 1
                    errors.append(f"Line {line_num} ({data.get('scheme_id')}): {validation_errors}")
                    continue

                repo.upsert_scheme(scheme_record, raw_payload=line_str)
                valid_count += 1
            except json.JSONDecodeError as e:
                error_count += 1
                errors.append(f"Line {line_num}: Invalid JSON syntax ({str(e)})")

    print(f"✅ Ingested {valid_count} validated schemes into database.")
    if errors:
        print(f"⚠️ Encountered {error_count} validation issues:")
        for err in errors:
            print(f"  - {err}")

    # Record in ingestion_logs table
    conn = get_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ingestion_logs (batch_name, records_imported, records_skipped, errors_json)
            VALUES (?, ?, ?, ?);
            """,
            ("Batch 1 Central Schemes", valid_count, error_count, json.dumps(errors)),
        )
    conn.close()

    return {"imported": valid_count, "errors": error_count, "error_details": errors}


def main():
    print("Starting Civicsaathi Data Ingestion Pipeline...")
    init_database()
    ingest_sources()
    result = ingest_schemes()
    print(f"Ingestion finished: {result['imported']} records imported.")


if __name__ == "__main__":
    main()
