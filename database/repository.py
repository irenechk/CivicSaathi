"""
Data repository layer for Civicsaathi.
Provides high-level queries and mutations for schemes, sources, documents, and profiles.
"""

import json
import sqlite3
from typing import List, Optional, Dict, Any
from pathlib import Path

from database.connection import get_connection, init_database
from database.models import SchemeRecord, CitizenProfile


class SchemeRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        init_database(db_path)

    def upsert_scheme(self, scheme: SchemeRecord, raw_payload: Optional[str] = None) -> None:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            # Check for existing record to preserve historical versioning
            cursor.execute("SELECT * FROM schemes WHERE scheme_id = ?", (scheme.scheme_id,))
            existing = cursor.fetchone()
            if existing:
                old_elig = existing["eligibility_json"]
                new_elig = json.dumps(scheme.eligibility.model_dump())
                old_benefit = existing["benefit_amount"]
                new_benefit = scheme.benefit_amount
                # If eligibility or benefits changed, preserve historical version
                if old_elig != new_elig or old_benefit != new_benefit:
                    cursor.execute("SELECT COUNT(*) FROM scheme_versions WHERE scheme_id = ?", (scheme.scheme_id,))
                    ver_count = cursor.fetchone()[0]
                    cursor.execute(
                        """
                        INSERT INTO scheme_versions (
                            scheme_id, version_tag, previous_eligibility_json, current_eligibility_json,
                            previous_benefits_json, current_benefits_json, source_document, change_notes,
                            verification_status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (
                            scheme.scheme_id,
                            f"v{ver_count + 1}.0",
                            old_elig,
                            new_elig,
                            old_benefit,
                            new_benefit,
                            scheme.guidelines_document_urls[0] if scheme.guidelines_document_urls else (scheme.official_source_urls[0] if scheme.official_source_urls else None),
                            f"Eligibility or benefit updated from {existing['verification_status']} baseline",
                            existing["verification_status"],
                        ),
                    )

            cursor.execute(
                """
                INSERT INTO schemes (
                    scheme_id, scheme_name, alternate_names_json, scheme_level, state_or_ut,
                    districts_json, ministry, department, description, objective,
                    target_beneficiaries_json, benefit_type_json, benefit_amount, benefit_frequency,
                    eligibility_json, exclusion_conditions_json, required_documents_json,
                    application_process_json, application_mode, official_application_url,
                    official_scheme_url, official_source_urls_json, guidelines_document_urls_json,
                    application_status, launch_date, last_updated_date, research_verified_date,
                    verification_status, source_notes_json, data_gaps_json, research_confidence,
                    raw_payload, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(scheme_id) DO UPDATE SET
                    scheme_name = excluded.scheme_name,
                    alternate_names_json = excluded.alternate_names_json,
                    scheme_level = excluded.scheme_level,
                    state_or_ut = excluded.state_or_ut,
                    districts_json = excluded.districts_json,
                    ministry = excluded.ministry,
                    department = excluded.department,
                    description = excluded.description,
                    objective = excluded.objective,
                    target_beneficiaries_json = excluded.target_beneficiaries_json,
                    benefit_type_json = excluded.benefit_type_json,
                    benefit_amount = excluded.benefit_amount,
                    benefit_frequency = excluded.benefit_frequency,
                    eligibility_json = excluded.eligibility_json,
                    exclusion_conditions_json = excluded.exclusion_conditions_json,
                    required_documents_json = excluded.required_documents_json,
                    application_process_json = excluded.application_process_json,
                    application_mode = excluded.application_mode,
                    official_application_url = excluded.official_application_url,
                    official_scheme_url = excluded.official_scheme_url,
                    official_source_urls_json = excluded.official_source_urls_json,
                    guidelines_document_urls_json = excluded.guidelines_document_urls_json,
                    application_status = excluded.application_status,
                    launch_date = excluded.launch_date,
                    last_updated_date = excluded.last_updated_date,
                    research_verified_date = excluded.research_verified_date,
                    verification_status = excluded.verification_status,
                    source_notes_json = excluded.source_notes_json,
                    data_gaps_json = excluded.data_gaps_json,
                    research_confidence = excluded.research_confidence,
                    raw_payload = excluded.raw_payload,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (
                    scheme.scheme_id,
                    scheme.scheme_name,
                    json.dumps(scheme.alternate_names),
                    scheme.scheme_level,
                    scheme.state_or_ut,
                    json.dumps(scheme.districts),
                    scheme.ministry,
                    scheme.department,
                    scheme.description,
                    scheme.objective,
                    json.dumps(scheme.target_beneficiaries),
                    json.dumps(scheme.benefit_type),
                    scheme.benefit_amount,
                    scheme.benefit_frequency,
                    json.dumps(scheme.eligibility.model_dump()),
                    json.dumps(scheme.exclusion_conditions),
                    json.dumps(scheme.required_documents),
                    json.dumps(scheme.application_process),
                    scheme.application_mode,
                    scheme.official_application_url,
                    scheme.official_scheme_url,
                    json.dumps(scheme.official_source_urls),
                    json.dumps(scheme.guidelines_document_urls),
                    scheme.application_status,
                    scheme.launch_date,
                    scheme.last_updated_date,
                    scheme.research_verified_date,
                    scheme.verification_status,
                    json.dumps(scheme.source_notes),
                    json.dumps(scheme.data_gaps),
                    scheme.research_confidence,
                    raw_payload or json.dumps(scheme.model_dump()),
                ),
            )
        conn.close()

    def get_scheme_by_id(self, scheme_id: str) -> Optional[SchemeRecord]:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM schemes WHERE scheme_id = ?", (scheme_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return self._row_to_scheme(row)

    # Alias for get_scheme_by_id
    get_scheme = get_scheme_by_id

    def list_all_schemes(self) -> List[SchemeRecord]:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM schemes ORDER BY scheme_id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_scheme(r) for r in rows]

    def count_schemes(self) -> int:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM schemes")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_metrics(self) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT verification_status, COUNT(*) FROM schemes GROUP BY verification_status")
        status_counts = dict(cursor.fetchall())
        cursor.execute("SELECT ministry, COUNT(*) FROM schemes WHERE ministry IS NOT NULL GROUP BY ministry")
        ministry_counts = dict(cursor.fetchall())
        cursor.execute("SELECT COUNT(*) FROM schemes")
        total = cursor.fetchone()[0]
        conn.close()
        return {
            "total_schemes": total,
            "status_counts": status_counts,
            "ministry_counts": ministry_counts,
        }

    def archive_scheme_version(
        self,
        scheme_id: str,
        version_tag: str,
        change_notes: str,
        source_doc: Optional[str] = None,
        created_by: str = "system",
    ) -> None:
        scheme = self.get_scheme_by_id(scheme_id)
        if not scheme:
            return
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO scheme_versions (
                    scheme_id, version_tag, previous_eligibility_json, current_eligibility_json,
                    previous_benefits_json, current_benefits_json, source_document, change_notes,
                    verification_status, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    scheme_id,
                    version_tag,
                    json.dumps(scheme.eligibility.model_dump()),
                    json.dumps(scheme.eligibility.model_dump()),
                    scheme.benefit_amount,
                    scheme.benefit_amount,
                    source_doc,
                    change_notes,
                    scheme.verification_status,
                    created_by,
                ),
            )
        conn.close()

    def get_scheme_versions(self, scheme_id: str) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scheme_versions WHERE scheme_id = ? ORDER BY version_id DESC", (scheme_id,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "version_id": r["version_id"],
                "scheme_id": r["scheme_id"],
                "version_tag": r["version_tag"],
                "previous_eligibility": json.loads(r["previous_eligibility_json"]) if r["previous_eligibility_json"] else {},
                "current_eligibility": json.loads(r["current_eligibility_json"]) if r["current_eligibility_json"] else {},
                "previous_benefits": r["previous_benefits_json"],
                "current_benefits": r["current_benefits_json"],
                "source_document": r["source_document"],
                "change_notes": r["change_notes"],
                "verification_status": r["verification_status"],
                "created_by": r["created_by"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    def flag_scheme_for_review(
        self,
        scheme_id: str,
        flag_type: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> int:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO admin_review_flags (scheme_id, flag_type, reason, details_json, status, flagged_at)
                VALUES (?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
                """,
                (scheme_id, flag_type, reason, json.dumps(details or {})),
            )
            flag_id = cursor.lastrowid
        conn.close()
        return flag_id

    def get_admin_flags(self, status: str = "pending") -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        if status == "all":
            cursor.execute("SELECT * FROM admin_review_flags ORDER BY flag_id DESC")
        else:
            cursor.execute("SELECT * FROM admin_review_flags WHERE status = ? ORDER BY flag_id DESC", (status,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "flag_id": r["flag_id"],
                "scheme_id": r["scheme_id"],
                "flag_type": r["flag_type"],
                "reason": r["reason"],
                "details": json.loads(r["details_json"]) if r["details_json"] else {},
                "status": r["status"],
                "flagged_at": r["flagged_at"],
                "resolved_at": r["resolved_at"],
                "resolved_by": r["resolved_by"],
            }
            for r in rows
        ]

    def resolve_admin_flag(self, flag_id: int, status: str = "resolved", resolved_by: str = "admin") -> bool:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE admin_review_flags
                SET status = ?, resolved_at = CURRENT_TIMESTAMP, resolved_by = ?
                WHERE flag_id = ?
                """,
                (status, resolved_by, flag_id),
            )
            affected = cursor.rowcount
        conn.close()
        return affected > 0

    def update_scheme_verification(self, scheme_id: str, new_status: str, admin_notes: Optional[str] = None) -> bool:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE schemes
                SET verification_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE scheme_id = ?
                """,
                (new_status, scheme_id),
            )
            affected = cursor.rowcount
        conn.close()
        return affected > 0

    def mark_scheme_outdated(self, scheme_id: str, reason: str, admin_id: str = "admin") -> bool:
        self.update_scheme_verification(scheme_id, "outdated")
        self.flag_scheme_for_review(scheme_id, "outdated", reason, {"marked_by": admin_id})
        return True

    def _row_to_scheme(self, row: sqlite3.Row) -> SchemeRecord:
        eligibility_data = json.loads(row["eligibility_json"]) if row["eligibility_json"] else {}
        return SchemeRecord(
            scheme_id=row["scheme_id"],
            scheme_name=row["scheme_name"],
            alternate_names=json.loads(row["alternate_names_json"]) if row["alternate_names_json"] else [],
            scheme_level=row["scheme_level"],
            state_or_ut=row["state_or_ut"],
            districts=json.loads(row["districts_json"]) if row["districts_json"] else [],
            ministry=row["ministry"],
            department=row["department"],
            description=row["description"],
            objective=row["objective"],
            target_beneficiaries=json.loads(row["target_beneficiaries_json"]) if row["target_beneficiaries_json"] else [],
            benefit_type=json.loads(row["benefit_type_json"]) if row["benefit_type_json"] else [],
            benefit_amount=row["benefit_amount"],
            benefit_frequency=row["benefit_frequency"],
            eligibility=eligibility_data,
            exclusion_conditions=json.loads(row["exclusion_conditions_json"]) if row["exclusion_conditions_json"] else [],
            required_documents=json.loads(row["required_documents_json"]) if row["required_documents_json"] else [],
            application_process=json.loads(row["application_process_json"]) if row["application_process_json"] else [],
            application_mode=row["application_mode"],
            official_application_url=row["official_application_url"],
            official_scheme_url=row["official_scheme_url"],
            official_source_urls=json.loads(row["official_source_urls_json"]) if row["official_source_urls_json"] else [],
            guidelines_document_urls=json.loads(row["guidelines_document_urls_json"]) if row["guidelines_document_urls_json"] else [],
            application_status=row["application_status"],
            launch_date=row["launch_date"],
            last_updated_date=row["last_updated_date"],
            research_verified_date=row["research_verified_date"],
            verification_status=row["verification_status"],
            source_notes=json.loads(row["source_notes_json"]) if row["source_notes_json"] else [],
            data_gaps=json.loads(row["data_gaps_json"]) if row["data_gaps_json"] else [],
            research_confidence=row["research_confidence"],
        )


class CitizenProfileRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        init_database(db_path)

    def save_profile(self, profile: CitizenProfile) -> None:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            profile_id = profile.user_id or "default_user"
            cursor.execute(
                """
                INSERT INTO citizen_profiles (
                    profile_id, user_id, full_name, language, state, district, age, gender,
                    occupation, annual_family_income, category, education_level,
                    is_disabled, has_bpl_card, owns_cultivable_land, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    full_name = excluded.full_name,
                    language = excluded.language,
                    state = excluded.state,
                    district = excluded.district,
                    age = excluded.age,
                    gender = excluded.gender,
                    occupation = excluded.occupation,
                    annual_family_income = excluded.annual_family_income,
                    category = excluded.category,
                    education_level = excluded.education_level,
                    is_disabled = excluded.is_disabled,
                    has_bpl_card = excluded.has_bpl_card,
                    owns_cultivable_land = excluded.owns_cultivable_land,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (
                    profile_id,
                    profile.user_id,
                    profile.full_name,
                    profile.language,
                    profile.state,
                    profile.district,
                    profile.age,
                    profile.gender,
                    profile.occupation,
                    profile.annual_family_income,
                    profile.category,
                    profile.education_level,
                    1 if profile.is_disabled else (0 if profile.is_disabled is False else None),
                    1 if profile.has_bpl_card else (0 if profile.has_bpl_card is False else None),
                    1 if profile.owns_cultivable_land else (0 if profile.owns_cultivable_land is False else None),
                ),
            )
        conn.close()

    def get_profile(self, user_id: str) -> Optional[CitizenProfile]:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM citizen_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return CitizenProfile(
            user_id=row["user_id"],
            full_name=row["full_name"] if "full_name" in row.keys() else None,
            language=row["language"] or "en",
            state=row["state"],
            district=row["district"],
            age=row["age"],
            gender=row["gender"],
            occupation=row["occupation"],
            annual_family_income=row["annual_family_income"],
            category=row["category"],
            education_level=row["education_level"],
            is_disabled=bool(row["is_disabled"]) if row["is_disabled"] is not None else None,
            has_bpl_card=bool(row["has_bpl_card"]) if row["has_bpl_card"] is not None else None,
            owns_cultivable_land=bool(row["owns_cultivable_land"]) if row["owns_cultivable_land"] is not None else None,
        )

    def delete_profile(self, user_id: str) -> None:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM citizen_profiles WHERE user_id = ?", (user_id,))
        conn.close()


class ConversationContextRepository:
    """Manages persistent multi-turn conversational context & scheme memory in SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        init_database(db_path)

    def get_context(self, user_id: str) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conversation_contexts WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return {"active_scheme_id": None, "active_scheme_name": None, "history": []}
        return {
            "active_scheme_id": row["active_scheme_id"],
            "active_scheme_name": row["active_scheme_name"],
            "history": json.loads(row["history_json"]) if row["history_json"] else [],
        }

    def set_active_scheme(self, user_id: str, scheme_id: str, scheme_name: str) -> None:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversation_contexts (user_id, active_scheme_id, active_scheme_name, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    active_scheme_id = excluded.active_scheme_id,
                    active_scheme_name = excluded.active_scheme_name,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (user_id, scheme_id, scheme_name),
            )
        conn.close()

    def add_turn(self, user_id: str, role: str, content: str, scheme_id: Optional[str] = None) -> None:
        current = self.get_context(user_id)
        history = current.get("history", [])
        history.append({"role": role, "content": content[:300], "scheme_id": scheme_id})
        # Keep last 8 turns to maintain tight context
        trimmed = history[-8:]

        active_id = scheme_id or current.get("active_scheme_id")
        active_name = current.get("active_scheme_name")

        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversation_contexts (user_id, active_scheme_id, active_scheme_name, history_json, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    active_scheme_id = COALESCE(excluded.active_scheme_id, conversation_contexts.active_scheme_id),
                    active_scheme_name = COALESCE(excluded.active_scheme_name, conversation_contexts.active_scheme_name),
                    history_json = excluded.history_json,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (user_id, active_id, active_name, json.dumps(trimmed)),
            )
        conn.close()

    def clear_context(self, user_id: str) -> None:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation_contexts WHERE user_id = ?", (user_id,))
        conn.close()


class CitizenDocumentRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        init_database(db_path)

    def get_citizen_documents(self, user_id: str) -> Dict[str, bool]:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT document_name, is_available FROM citizen_documents WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return {r["document_name"]: bool(r["is_available"]) for r in rows}

    def set_document_status(self, user_id: str, document_name: str, is_available: bool = True) -> None:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO citizen_documents (user_id, document_name, is_available, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, document_name) DO UPDATE SET
                    is_available = excluded.is_available,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (user_id, document_name, 1 if is_available else 0),
            )
        conn.close()

    def toggle_document_status(self, user_id: str, document_name: str) -> bool:
        current = self.get_citizen_documents(user_id).get(document_name, False)
        new_val = not current
        self.set_document_status(user_id, document_name, new_val)
        return new_val

    def clear_documents(self, user_id: str) -> None:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM citizen_documents WHERE user_id = ?", (user_id,))
        conn.close()


class CitizenSavedSchemeRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        init_database(db_path)

    def save_scheme(self, user_id: str, scheme_id: str) -> None:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO citizen_saved_schemes (user_id, scheme_id, saved_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, scheme_id),
            )
        conn.close()

    def remove_saved_scheme(self, user_id: str, scheme_id: str) -> None:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM citizen_saved_schemes WHERE user_id = ? AND scheme_id = ?",
                (user_id, scheme_id),
            )
        conn.close()

    def get_saved_schemes(self, user_id: str) -> List[str]:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT scheme_id FROM citizen_saved_schemes WHERE user_id = ? ORDER BY saved_at DESC", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [r["scheme_id"] for r in rows]

    def record_view_history(self, user_id: str, scheme_id: str) -> None:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO citizen_view_history (user_id, scheme_id, viewed_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, scheme_id),
            )
        conn.close()

    def get_view_history(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT v.scheme_id, s.scheme_name, v.viewed_at
            FROM citizen_view_history v
            LEFT JOIN schemes s ON v.scheme_id = s.scheme_id
            WHERE v.user_id = ?
            ORDER BY v.history_id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {"scheme_id": r["scheme_id"], "scheme_name": r["scheme_name"] or r["scheme_id"], "viewed_at": r["viewed_at"]}
            for r in rows
        ]

    def clear_user_data(self, user_id: str) -> None:
        conn = get_connection(self.db_path)
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM citizen_saved_schemes WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM citizen_view_history WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM citizen_documents WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM conversation_contexts WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM citizen_profiles WHERE user_id = ?", (user_id,))
        conn.close()
