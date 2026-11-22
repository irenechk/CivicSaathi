"""
Tests for Civicsaathi Step-by-Step Citizen Interview FSM and Enhanced RAG Follow-up Question Answering.
"""

import pytest
from database.models import CitizenProfile
from database.repository import CitizenProfileRepository, SchemeRepository
from rag.document_processor import DocumentProcessor
from rag.embeddings import LocalEmbeddingEngine
from rag.vector_store import LocalVectorStore
from rag.retriever import HybridRetriever
from rag.answer_generator import AnswerGenerator
from handlers.interview import (
    get_name_keyboard,
    get_state_keyboard,
    get_age_keyboard,
    get_gender_keyboard,
    get_occupation_keyboard,
    get_income_keyboard,
    get_category_keyboard,
)


def test_profile_with_fullname_persistence(tmp_path):
    """Verify full_name is correctly saved and retrieved from SQLite."""
    db_file = tmp_path / "test_profile.db"
    repo = CitizenProfileRepository(db_path=db_file)

    profile = CitizenProfile(
        user_id="user_9988",
        full_name="Aashika Pandey",
        language="hi",
        state="Maharashtra",
        age=28,
        gender="female",
        occupation="Farmer",
        annual_family_income=150000.0,
        category="General",
    )
    repo.save_profile(profile)

    loaded = repo.get_profile("user_9988")
    assert loaded is not None
    assert loaded.full_name == "Aashika Pandey"
    assert loaded.state == "Maharashtra"
    assert loaded.occupation == "Farmer"
    assert loaded.annual_family_income == 150000.0
    assert loaded.category == "General"


def test_interview_keyboards_multilingual():
    """Verify all 7 step keyboards generate valid buttons across English, Hindi, and Marathi."""
    for lang in ["en", "hi", "mr"]:
        kb_name = get_name_keyboard(lang)
        assert len(kb_name.inline_keyboard[0]) >= 1

        kb_state = get_state_keyboard(lang)
        flat_state = [b for r in kb_state.inline_keyboard for b in r]
        assert len(flat_state) >= 8

        kb_age = get_age_keyboard(lang)
        assert len(kb_age.inline_keyboard) == 2

        kb_gender = get_gender_keyboard(lang)
        assert len(kb_gender.inline_keyboard[0]) == 2

        kb_occ = get_occupation_keyboard(lang)
        flat_occ = [b for r in kb_occ.inline_keyboard for b in r]
        assert len(flat_occ) == 6

        kb_inc = get_income_keyboard(lang)
        flat_inc = [b for r in kb_inc.inline_keyboard for b in r]
        assert len(flat_inc) == 6

        kb_cat = get_category_keyboard(lang)
        flat_cat = [b for r in kb_cat.inline_keyboard for b in r]
        assert len(flat_cat) == 5


def test_rag_followup_scheme_resolution():
    """Verify HybridRetriever resolves specific follow-up questions accurately."""
    repo = SchemeRepository()
    schemes = repo.list_all_schemes()
    assert len(schemes) == 30

    processor = DocumentProcessor()
    chunks = []
    for s in schemes:
        chunks.extend(processor.process_scheme_record(s))

    store = LocalVectorStore(LocalEmbeddingEngine())
    store.add_chunks(chunks)
    retriever = HybridRetriever(store)
    generator = AnswerGenerator()

    # 1. How do I apply for PM-KISAN?
    res_pmkisan = retriever.retrieve("How do I apply for PM-KISAN?", top_k=3)
    assert len(res_pmkisan) > 0
    top_scheme_name = res_pmkisan[0]["metadata"]["scheme_name"]
    assert "Kisan" in top_scheme_name or "PM-KISAN" in str(res_pmkisan[0]["metadata"].get("alternate_names"))

    ans_pmkisan = generator.generate_answer("How do I apply for PM-KISAN?", retrieved_passages=res_pmkisan, language="en")
    assert "Pradhan Mantri Kisan Samman Nidhi" in ans_pmkisan["answer"]
    assert len(ans_pmkisan["citations"]) > 0

    # 2. What documents are required for KCC?
    res_kcc = retriever.retrieve("What documents are required for KCC?", top_k=3)
    assert len(res_kcc) > 0
    assert "Kisan Credit Card" in res_kcc[0]["metadata"]["scheme_name"]

    ans_kcc = generator.generate_answer("What documents are required for KCC?", passages=res_kcc, language="en")
    assert "Kisan Credit Card" in ans_kcc["answer"]

    # 3. What is PMSBY?
    res_pmsby = retriever.retrieve("What is PMSBY?", top_k=3)
    assert len(res_pmsby) > 0
    assert "Suraksha Bima" in res_pmsby[0]["metadata"]["scheme_name"]

    # 4. Multilingual generation (Hindi & Marathi)
    ans_hi = generator.generate_answer("PM-KISAN लाभ", retrieved_passages=res_pmkisan, language="hi")
    assert "सत्यापन स्थिति" in ans_hi["answer"]

    ans_mr = generator.generate_answer("PM-KISAN माहिती", retrieved_passages=res_pmkisan, language="mr")
    assert "पडताळणी स्थिती" in ans_mr["answer"]


def test_multiturn_conversational_context_memory(tmp_path):
    """Verify follow-up questions without scheme name maintain active scheme context."""
    from handlers.help import get_telegram_rag, is_followup_query
    from database.repository import ConversationContextRepository

    db_file = tmp_path / "test_ctx.db"
    ctx_repo = ConversationContextRepository(db_path=db_file)
    user_id = "test_user_ctx_456"

    # Set active scheme as PM-KISAN
    ctx_repo.set_active_scheme(user_id, "GOI-CEN-004", "Pradhan Mantri Kisan Samman Nidhi")

    # Citizen asks anaphora query without scheme name
    followup_q = "How do I apply for this scheme?"
    assert is_followup_query(followup_q) is True

    ctx = ctx_repo.get_context(user_id)
    assert ctx["active_scheme_name"] == "Pradhan Mantri Kisan Samman Nidhi"

    # Query rewriting
    effective_q = f"{followup_q} {ctx['active_scheme_name']}"

    retriever, generator = get_telegram_rag()
    retrieved = retriever.retrieve(effective_q, top_k=2)

    ans = generator.generate_answer(followup_q, retrieved_passages=retrieved, language="en", context=ctx)
    assert "Pradhan Mantri Kisan Samman Nidhi" in ans["answer"]
    assert "How to Apply" in ans["answer"] or "Application" in ans["answer"]
    assert len(ans["citations"]) > 0


def test_pinpoint_specific_question_answering():
    """Verify that specific atomic queries return targeted data rather than dumping all scheme info."""
    from rag.answer_generator import AnswerGenerator
    from database.repository import SchemeRepository
    from database.models import CitizenProfile

    generator = AnswerGenerator()
    repo = SchemeRepository()
    kcc_scheme = repo.get_scheme_by_id("GOI-CEN-005")
    pmsby_scheme = repo.get_scheme_by_id("GOI-CEN-003")

    passages_kcc = [{
        "text": kcc_scheme.description,
        "metadata": {"scheme_id": "GOI-CEN-005", "scheme_name": kcc_scheme.scheme_name}
    }]
    passages_pmsby = [{
        "text": pmsby_scheme.description,
        "metadata": {"scheme_id": "GOI-CEN-003", "scheme_name": pmsby_scheme.scheme_name}
    }]

    # 1. Website Link Query: Must return portal link only, without full overview dump
    ans_link = generator.generate_answer("What is the official website link for KCC?", passages=passages_kcc, language="en")
    assert "Official Website for" in ans_link["answer"]
    assert "Official Portal" in ans_link["answer"]
    assert "Overview:" not in ans_link["answer"]

    # 2. Age Query: Must return age criteria only
    ans_age = generator.generate_answer("What is the age limit for PMSBY?", passages=passages_pmsby, language="en")
    assert "Age Criteria for" in ans_age["answer"]
    assert "18 to 70 years" in ans_age["answer"]
    assert "Overview:" not in ans_age["answer"]

    # 3. Benefit Amount Query: Must return benefit amount only
    ans_amt = generator.generate_answer("How much money do farmers get under PM-KISAN?", passages=[{
        "text": "PM-KISAN benefit",
        "metadata": {"scheme_id": "GOI-CEN-004", "scheme_name": "PM-KISAN"}
    }], language="en")
    assert "Benefit Amount for" in ans_amt["answer"]
    assert "Financial Support" in ans_amt["answer"]
    assert "Overview:" not in ans_amt["answer"]

    # 4. Premium / Rate Query: Must return exact premium
    ans_prem = generator.generate_answer("What is the annual premium for PMSBY?", passages=passages_pmsby, language="en")
    assert "Rate & Premium for" in ans_prem["answer"]
    assert "₹20 per year" in ans_prem["answer"]
    assert "Overview:" not in ans_prem["answer"]

    # 5. Documents Query: Must return document list only
    ans_docs = generator.generate_answer("What documents are required for KCC?", passages=passages_kcc, language="en")
    assert "Documents Required for" in ans_docs["answer"]
    assert "Application Mode:" in ans_docs["answer"]
    assert "Overview:" not in ans_docs["answer"]

    # 6. Apply Query: Must return step-by-step application instructions only
    ans_apply = generator.generate_answer("How do I apply for KCC?", passages=passages_kcc, language="en")
    assert "How to Apply for" in ans_apply["answer"]
    assert "Application Procedure" in ans_apply["answer"]
    assert "Overview:" not in ans_apply["answer"]

    # 7. Personalized Eligibility Check
    profile = CitizenProfile(full_name="Ramesh", age=42, occupation="Farmer", annual_family_income=90000.0)
    ans_elig = generator.generate_answer("Am I eligible for KCC?", passages=passages_kcc, language="en", profile=profile)
    assert "Personalized Eligibility for Ramesh" in ans_elig["answer"]
    assert "Eligibility Criteria for" in ans_elig["answer"]
    assert "Overview:" not in ans_elig["answer"]


def test_all_interactive_callbacks_and_keyboards():
    """Verify all interactive buttons, callbacks, and keyboards function correctly."""
    from handlers.interview import get_assessment_completion_keyboard
    from handlers.help import get_scheme_quick_actions
    from handlers.start import get_main_menu_keyboard
    from services.comparison import SchemeComparisonService
    from services.readiness import ApplicationReadinessTracker
    from services.dashboard import CitizenDashboardService
    from services.privacy import PrivacyGuard
    from database.repository import SchemeRepository

    for lang in ["en", "hi", "mr"]:
        # 1. Assessment completion keyboard
        comp_kb = get_assessment_completion_keyboard(lang)
        flat_comp = [b for row in comp_kb.inline_keyboard for b in row]
        assert len(flat_comp) == 4
        comp_callbacks = [b.callback_data for b in flat_comp]
        assert "menu_compare" in comp_callbacks
        assert "menu_readiness" in comp_callbacks
        assert "menu_profile" in comp_callbacks
        assert "menu_schemes" in comp_callbacks

        # 2. Scheme quick actions
        quick_kb = get_scheme_quick_actions("GOI-CEN-004", lang)
        flat_quick = [b for row in quick_kb.inline_keyboard for b in row]
        assert len(flat_quick) == 5
        quick_callbacks = [b.callback_data for b in flat_quick]
        assert "act_apply:GOI-CEN-004" in quick_callbacks
        assert "act_docs:GOI-CEN-004" in quick_callbacks
        assert "act_amt:GOI-CEN-004" in quick_callbacks
        assert "act_ready:GOI-CEN-004" in quick_callbacks
        assert "act_save:GOI-CEN-004" in quick_callbacks

        # 3. Main menu 7 buttons (standard) and 9 buttons (advanced)
        mm_7 = get_main_menu_keyboard(lang, include_advanced=False)
        assert len([b for r in mm_7.inline_keyboard for b in r]) == 7
        mm_9 = get_main_menu_keyboard(lang, include_advanced=True)
        assert len([b for r in mm_9.inline_keyboard for b in r]) == 9

    # 4. Service end-to-end functionality
    comparator = SchemeComparisonService()
    comp_rep = comparator.compare_schemes(["PM-KISAN", "KCC"], language="en")
    assert len(comp_rep.schemes) == 2
    comp_text = comparator.format_comparison_telegram(comp_rep, language="en")
    assert "PM-KISAN" in comp_text

    scheme = SchemeRepository().get_scheme_by_id("GOI-CEN-004")
    tracker = ApplicationReadinessTracker()
    ready_rep = tracker.evaluate_readiness(scheme, language="en")
    ready_text = tracker.format_readiness_telegram(ready_rep, language="en")
    assert "Readiness Indicator:" in ready_text
    assert "does not guarantee government approval" in ready_text

    dash_service = CitizenDashboardService()
    dash_data = dash_service.get_dashboard_data("test_user_dash", language="en")
    dash_text = dash_service.format_dashboard_telegram(dash_data, language="en")
    assert "Citizen Profile Dashboard" in dash_text

    # 5. Privacy guard protection
    sanitized = PrivacyGuard.check_sensitive_content("My Aadhaar is 5566 7788 9900 and OTP 123456", language="en")
    assert sanitized["has_sensitive_data"] is True
    assert "5566" not in sanitized["sanitized_text"]
    assert "123456" not in sanitized["sanitized_text"]


@pytest.mark.anyio
async def test_groq_service_and_resilient_fallback():
    """Verify GroqService configuration, method signatures, and offline resilience."""
    from services.groq_service import GroqService

    # 1. Unconfigured instance
    empty_groq = GroqService(api_key="")
    assert empty_groq.is_configured is False
    assert await empty_groq.transcribe_audio(b"dummy") is None
    assert await empty_groq.synthesize_scheme_answer("test", []) is None

    # 2. Configured instance with the integrated key
    active_groq = GroqService()
    assert active_groq.is_configured is True
    assert active_groq.api_key.startswith("gsk_")

    # 3. Empty retrieved passages returns None (safeguard)
    empty_passages_ans = await active_groq.synthesize_scheme_answer("Query without evidence", [])
    assert empty_passages_ans is None


