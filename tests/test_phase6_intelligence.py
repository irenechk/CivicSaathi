"""
Civicsaathi Phase 6 Comprehensive Test Suite: Advanced Citizen Intelligence and Trust.

Tests cover:
1. Source-backed answers with complete official metadata (Name, URL, Document, Section, Verified Date, Status)
2. Handling of unverified, outdated, and conflicting sources
3. Scheme versioning and historical condition preservation
4. Missing evidence RAG safeguards
5. Multi-scheme comparison matrix (benefits, eligibility, docs, process, sources)
6. Application readiness tracker and legal disclaimers
7. Citizen dashboard and profile updates
8. Full data deletion sovereignty (DPDP Act compliance)
9. Privacy guard against credential collection (Aadhaar, OTP, passwords, banking)
10. Admin verification governance and unverified data quarantine
"""

import pytest
from pathlib import Path

from database.models import CitizenProfile, SchemeRecord, EligibilityCriteria
from database.connection import init_database
from database.repository import (
    SchemeRepository,
    CitizenProfileRepository,
    CitizenDocumentRepository,
    CitizenSavedSchemeRepository,
    ConversationContextRepository,
)
from rag.retriever import HybridRetriever
from rag.answer_generator import AnswerGenerator
from services.comparison import SchemeComparisonService
from services.readiness import ApplicationReadinessTracker
from services.dashboard import CitizenDashboardService
from services.admin import AdminVerificationService
from services.privacy import PrivacyGuard


@pytest.fixture
def test_db(tmp_path):
    """Initializes isolated SQLite database for testing."""
    db_file = tmp_path / "test_phase6.db"
    init_database(db_file)
    return db_file


# 1. Source-Backed Answers with Complete Provenance
def test_source_backed_answers_provenance(test_db):
    generator = AnswerGenerator()
    passages = [{
        "text": "PM-KISAN provides INR 6,000 yearly in 3 equal instalments.",
        "metadata": {
            "scheme_id": "GOI-CEN-004",
            "scheme_name": "PM-KISAN",
            "source_url": "https://pmkisan.gov.in",
            "document_title": "PM-KISAN Operational Guidelines 2026",
            "section": "Disbursement Cadence",
            "verified_date": "2026-11-21",
            "verification_status": "partially_verified",
        }
    }]
    ans = generator.generate_answer("How much benefit under PM-KISAN?", passages=passages, language="en")
    assert "PM-KISAN" in ans["answer"]
    assert len(ans["citations"]) == 1
    c = ans["citations"][0]
    assert c["scheme_name"] is not None
    assert "pmkisan.gov.in" in c["source_url"] or "myscheme.gov.in" in c["source_url"]
    assert c["document_title"] is not None
    assert c["section"] is not None
    assert c["verified_date"] is not None
    assert c["verification_status"] in ("verified", "partially_verified")


# 2. Outdated and Conflicting Sources Flagging
def test_outdated_and_conflicting_sources_flagging(test_db):
    repo = SchemeRepository(db_path=test_db)
    # Insert dummy scheme
    s = SchemeRecord(
        scheme_id="TEST-001",
        scheme_name="Test Subsidy Scheme",
        description="A test scheme with changing guidelines",
        verification_status="verified",
    )
    repo.upsert_scheme(s)

    admin = AdminVerificationService(repository=repo)
    # Admin flags outdated scheme
    flag_id = admin.flag_outdated_or_conflicting(
        scheme_id="TEST-001",
        flag_type="outdated",
        reason="Income ceiling lowered in 2026 budget gazette",
        admin_id="auditor_01",
    )
    assert flag_id > 0

    updated_scheme = repo.get_scheme_by_id("TEST-001")
    assert updated_scheme.verification_status == "outdated"

    flags = admin.get_scraper_and_review_logs()
    assert len(flags) >= 1
    assert flags[0]["flag_type"] == "outdated"


# 3. Scheme Versioning and Historical Condition Preservation
def test_scheme_versioning_and_historical_preservation(test_db):
    repo = SchemeRepository(db_path=test_db)
    s = SchemeRecord(
        scheme_id="TEST-VER-01",
        scheme_name="Scholarship Scheme",
        description="Higher education scholarship",
        benefit_amount="INR 20,000 per year",
        eligibility=EligibilityCriteria(age_min=18, age_max=25, income_limit=250000.0),
        verification_status="verified",
    )
    repo.upsert_scheme(s)

    # Update scheme with new eligibility rules in 2026
    s_v2 = SchemeRecord(
        scheme_id="TEST-VER-01",
        scheme_name="Scholarship Scheme",
        description="Higher education scholarship revised",
        benefit_amount="INR 30,000 per year",
        eligibility=EligibilityCriteria(age_min=18, age_max=28, income_limit=350000.0),
        verification_status="verified",
    )
    # Upserting should automatically archive the v1 state
    repo.upsert_scheme(s_v2)

    versions = repo.get_scheme_versions("TEST-VER-01")
    assert len(versions) >= 1
    old_v = versions[0]
    assert old_v["previous_eligibility"]["income_limit"] == 250000.0
    assert old_v["current_eligibility"]["income_limit"] == 350000.0
    assert old_v["previous_benefits"] == "INR 20,000 per year"
    assert old_v["current_benefits"] == "INR 30,000 per year"


# 4. Missing Evidence RAG Safeguard
def test_missing_evidence_rag_safeguard():
    generator = AnswerGenerator()
    # Query with no passages
    res = generator.generate_answer("What is the grant for Mars rover farming?", passages=[], language="en")
    assert "unavailable" in res["answer"].lower() or "verification" in res["answer"].lower()


# 5. Multiple Scheme Comparison Matrix
def test_multiple_scheme_comparison(test_db):
    repo = SchemeRepository(db_path=test_db)
    s1 = SchemeRecord(
        scheme_id="GOI-CEN-004",
        scheme_name="Pradhan Mantri Kisan Samman Nidhi",
        alternate_names=["PM-KISAN"],
        description="Direct income support of ₹6,000/year to landholding farmers.",
        benefit_amount="₹6,000 per year",
        benefit_frequency="Three 4-monthly instalments",
        eligibility=EligibilityCriteria(occupation=["Farmer"]),
        required_documents=["[Mandatory] Aadhaar Card", "[Mandatory] Land Record"],
        application_mode="online_and_offline",
        verification_status="partially_verified",
    )
    s2 = SchemeRecord(
        scheme_id="GOI-CEN-008",
        scheme_name="Kisan Credit Card",
        alternate_names=["KCC"],
        description="Concessional short-term crop loans up to ₹3,00,000 at 4% effective interest.",
        benefit_amount="Credit limit up to ₹3,00,000",
        benefit_frequency="Revolving credit",
        eligibility=EligibilityCriteria(occupation=["Farmer", "Fisherman"]),
        required_documents=["[Mandatory] Aadhaar Card", "[Mandatory] Bank Account", "[Mandatory] Land Record"],
        application_mode="online_and_offline",
        verification_status="verified",
    )
    repo.upsert_scheme(s1)
    repo.upsert_scheme(s2)

    comparator = SchemeComparisonService(repository=repo)
    report = comparator.compare_schemes(["PM-KISAN", "KCC"], language="en")
    assert len(report.schemes) == 2
    names = [item.scheme_name for item in report.schemes]
    assert any("PM-KISAN" in n for n in names)
    assert any("KCC" in n for n in names)

    formatted = comparator.format_comparison_telegram(report, language="en")
    assert "Scheme Comparison Report" in formatted
    assert "Financial Benefits:" in formatted
    assert "Geographical Scope:" in formatted


# 6. Application Readiness Tracker and Legal Disclaimer
def test_application_readiness_tracker(test_db):
    scheme_repo = SchemeRepository(db_path=test_db)
    doc_repo = CitizenDocumentRepository(db_path=test_db)

    scheme = SchemeRecord(
        scheme_id="TEST-READY-01",
        scheme_name="PM Kisan Samman",
        description="Farmer support",
        required_documents=[
            "[Mandatory] Aadhaar Card",
            "[Mandatory] Bank Account Passbook",
            "[Mandatory] Land Ownership Record",
            "[Conditional] Caste Certificate",
        ],
        verification_status="verified",
    )
    scheme_repo.upsert_scheme(scheme)

    # Citizen has Aadhaar and Bank Passbook ready, but missing Land Record
    user_id = "citizen_readiness_01"
    doc_repo.set_document_status(user_id, "Aadhaar Card", True)
    doc_repo.set_document_status(user_id, "Bank Account Passbook", True)

    tracker = ApplicationReadinessTracker(scheme_repo=scheme_repo, doc_repo=doc_repo)
    report = tracker.evaluate_readiness(scheme, user_id=user_id, language="en")

    assert report.mandatory_count == 3
    assert report.available_count == 2
    assert "Land Ownership Record" in report.missing_mandatory
    assert "Caste Certificate" in report.conditional_documents
    assert report.readiness_percentage == 66.7
    assert report.readiness_level == "Moderate"
    # Never imply readiness guarantees approval
    assert "does not guarantee" in report.disclaimer.lower()

    # Formatted Telegram representation
    card = tracker.format_readiness_telegram(report, language="en")
    assert "Document Readiness Indicator:" in card
    assert "Disclaimer:" in card


# 7. Citizen Profile Updates and Dashboard Aggregation
def test_citizen_dashboard_and_profile_updates(test_db):
    profile_repo = CitizenProfileRepository(db_path=test_db)
    saved_repo = CitizenSavedSchemeRepository(db_path=test_db)
    scheme_repo = SchemeRepository(db_path=test_db)

    s = SchemeRecord(
        scheme_id="GOI-CEN-004",
        scheme_name="PM-KISAN",
        description="Farmer income support",
        benefit_amount="INR 6,000 per year",
        verification_status="partially_verified",
    )
    scheme_repo.upsert_scheme(s)

    user_id = "user_dash_777"
    profile = CitizenProfile(
        user_id=user_id,
        full_name="Rajesh Kumar",
        state="Uttar Pradesh",
        age=38,
        occupation="Farmer",
        annual_family_income=120000.0,
        category="OBC",
    )
    profile_repo.save_profile(profile)
    saved_repo.save_scheme(user_id, "GOI-CEN-004")
    saved_repo.record_view_history(user_id, "GOI-CEN-004")

    dash_service = CitizenDashboardService(
        profile_repo=profile_repo,
        saved_repo=saved_repo,
        scheme_repo=scheme_repo,
    )
    dash_data = dash_service.get_dashboard_data(user_id, language="en")
    assert dash_data.profile.full_name == "Rajesh Kumar"
    assert len(dash_data.saved_schemes) == 1
    assert dash_data.saved_schemes[0]["scheme_id"] == "GOI-CEN-004"
    assert len(dash_data.recently_viewed) >= 1

    formatted_dash = dash_service.format_dashboard_telegram(dash_data, language="en")
    assert "Rajesh Kumar" in formatted_dash
    assert "Saved Schemes / Bookmarks" in formatted_dash


# 8. Data Deletion Lifecycle (DPDP Act Compliance)
def test_data_deletion_lifecycle(test_db):
    scheme_repo = SchemeRepository(db_path=test_db)
    profile_repo = CitizenProfileRepository(db_path=test_db)
    saved_repo = CitizenSavedSchemeRepository(db_path=test_db)
    doc_repo = CitizenDocumentRepository(db_path=test_db)
    ctx_repo = ConversationContextRepository(db_path=test_db)

    # Insert scheme so foreign key is satisfied
    scheme_repo.upsert_scheme(SchemeRecord(scheme_id="GOI-CEN-001", scheme_name="PMMVY", description="Maternity scheme"))

    user_id = "user_delete_999"
    profile_repo.save_profile(CitizenProfile(user_id=user_id, full_name="Sita Devi", age=32))
    saved_repo.save_scheme(user_id, "GOI-CEN-001")
    doc_repo.set_document_status(user_id, "Aadhaar Card", True)
    ctx_repo.set_active_scheme(user_id, "GOI-CEN-001", "PMMVY")

    # Citizen triggers full deletion
    saved_repo.clear_user_data(user_id)

    assert profile_repo.get_profile(user_id) is None
    assert len(saved_repo.get_saved_schemes(user_id)) == 0
    assert len(doc_repo.get_citizen_documents(user_id)) == 0
    assert ctx_repo.get_context(user_id)["active_scheme_id"] is None


# 9. Privacy Guard: Sensitive Credential Blocking
def test_privacy_guard_credential_blocking():
    # Aadhaar number detection and masking
    text_with_aadhaar = "My Aadhaar is 5482 9182 3491 and I am a farmer"
    res_aadhaar = PrivacyGuard.check_sensitive_content(text_with_aadhaar, language="en")
    assert res_aadhaar["has_sensitive_data"] is True
    assert "Aadhaar Number" in res_aadhaar["detected_types"]
    assert "5482 9182 3491" not in res_aadhaar["sanitized_text"]
    assert "[REDACTED_AADHAAR]" in res_aadhaar["sanitized_text"]
    assert "Security Advisory" in res_aadhaar["warning"]

    # OTP detection and masking
    text_with_otp = "Your OTP is 849201 for login"
    res_otp = PrivacyGuard.check_sensitive_content(text_with_otp, language="hi")
    assert res_otp["has_sensitive_data"] is True
    assert "OTP / Security Code" in res_otp["detected_types"]
    assert "849201" not in res_otp["sanitized_text"]
    assert "सुरक्षा चेतावनी" in res_otp["warning"]

    # Bank account detection and masking
    text_with_bank = "Deposit subsidy into my bank account 1092837461928"
    res_bank = PrivacyGuard.check_sensitive_content(text_with_bank, language="mr")
    assert res_bank["has_sensitive_data"] is True
    assert "Bank Account / Card Details" in res_bank["detected_types"]
    assert "1092837461928" not in res_bank["sanitized_text"]
    assert "सुरक्षा सूचना" in res_bank["warning"]


# 10. Admin Verification Workflow and Unverified Data Quarantine
def test_admin_verification_workflow(test_db):
    repo = SchemeRepository(db_path=test_db)
    admin = AdminVerificationService(repository=repo)

    # Scraped scheme enters as unverified
    scraped = SchemeRecord(
        scheme_id="SCRAPE-001",
        scheme_name="Unverified Scraped Solar Subsidy",
        description="Freshly crawled scheme from portal",
        verification_status="unverified",
        research_confidence="low",
    )
    repo.upsert_scheme(scraped)

    pending = admin.get_pending_schemes()
    pending_ids = [p["scheme_id"] for p in pending]
    assert "SCRAPE-001" in pending_ids

    # Unverified scraped data must NEVER automatically become verified without explicit admin approval
    s_before = repo.get_scheme_by_id("SCRAPE-001")
    assert s_before.verification_status == "unverified"

    # Human admin conducts verification and approves
    admin.verify_and_approve_scheme(
        scheme_id="SCRAPE-001",
        admin_id="senior_admin_01",
        verified_date="2026-11-22",
        admin_notes="Primary Gazette Notification G.S.R. 412 verified on ministry site.",
    )

    s_after = repo.get_scheme_by_id("SCRAPE-001")
    assert s_after.verification_status == "verified"
    assert s_after.research_confidence == "high"
    assert s_after.research_verified_date == "2026-11-22"
    assert any("senior_admin_01" in n for n in s_after.source_notes)
