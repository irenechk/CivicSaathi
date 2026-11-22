"""
Comprehensive automated test suite for Civicsaathi Platform (20 Phase 11 test cases).
"""

import sys
import tempfile
from pathlib import Path
import pytest
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.models import SchemeRecord, CitizenProfile
from database.connection import init_database
from database.repository import SchemeRepository, CitizenProfileRepository
from database.ingest_raw_data import ingest_schemes, ingest_sources
from scraper.source_registry import SourceRegistry
from scraper.crawler import GovernmentCrawler
from scraper.html_extractor import HtmlExtractor
from scraper.pdf_extractor import PdfExtractor
from scraper.deduplicator import Deduplicator
from scraper.validator import SchemeValidator
from rag.embeddings import LocalEmbeddingEngine
from rag.vector_store import LocalVectorStore
from rag.retriever import HybridRetriever
from rag.answer_generator import AnswerGenerator
from eligibility.rule_engine import RuleEngine
from eligibility.evaluator import SchemeEvaluator
from eligibility.explanations import EligibilityExplainer
from chatbot.profile_extractor import ProfileExtractor
from chatbot.conversation import ConversationManager
from services.scheme_search import SchemeSearchService
from services.recommendation import RecommendationService
from services.helpline import HelplineService
from ui.components import get_theme_css


# 1. JSONL Import Test
def test_01_jsonl_import():
    result = ingest_schemes()
    assert result["imported"] == 30
    assert result["errors"] == 0


# 2. CSV Import Test
def test_02_csv_import():
    count = ingest_sources()
    assert count == 25


# 3. PDF Text Extraction Test
def test_03_pdf_extraction():
    # Test using pypdf reader on synthetic or mock pdf
    from pypdf import PdfWriter
    import io
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    pdf_bytes_io = io.BytesIO()
    writer.write(pdf_bytes_io)
    pdf_bytes = pdf_bytes_io.getvalue()

    result = PdfExtractor.extract_from_bytes(pdf_bytes)
    assert result["total_pages"] == 1
    assert "pages" in result


# 4. HTML Extraction Test
def test_04_html_extraction():
    html_sample = """
    <html><head><title>PM-KISAN Scheme</title></head>
    <body><h1>Eligibility</h1><p>All landholding farmers families having cultivable land are eligible.</p>
    <a href="/guidelines.pdf">Download Guidelines</a></body></html>
    """
    extracted = HtmlExtractor.extract_scheme_page(html_sample, base_url="https://myscheme.gov.in")
    assert extracted["title"] == "PM-KISAN Scheme"
    assert "Eligibility" in extracted["headings"]
    assert len(extracted["pdf_links"]) == 1
    assert extracted["pdf_links"][0]["url"] == "https://myscheme.gov.in/guidelines.pdf"


# 5. Duplicate Detection Test
def test_05_duplicate_detection():
    existing = [
        {"scheme_name": "Pradhan Mantri Awas Yojana - Urban", "alternate_names": ["PMAY-U"]}
    ]
    dups = Deduplicator.find_potential_duplicates("PMAY-U 2.0 Housing Mission", existing, threshold=0.4)
    assert len(dups) > 0


# 6. Source Provenance Test
def test_06_source_provenance():
    repo = SchemeRepository()
    scheme = repo.get_scheme_by_id("GOI-CEN-001")
    assert scheme is not None
    assert scheme.official_scheme_url == "https://www.myscheme.gov.in/schemes/pmmvy"
    assert len(scheme.official_source_urls) > 0


# 7. Local Embeddings Test
def test_07_local_embeddings():
    engine = LocalEmbeddingEngine(max_features=128)
    texts = ["crop insurance for farmers", "maternity benefit for pregnant women", "student loan"]
    vecs = engine.embed_documents(texts)
    assert vecs.shape == (3, 128)
    q_vec = engine.embed_query("farmer insurance")
    assert len(q_vec) == 128


# 8. Vector Search Test
def test_08_vector_search():
    engine = LocalEmbeddingEngine(max_features=64)
    store = LocalVectorStore(engine)
    chunks = [
        {"text": "Crop insurance scheme for farmers facing drought", "metadata": {"scheme_id": "PMFBY", "verification_status": "verified"}},
        {"text": "Maternity cash assistance for pregnant mothers", "metadata": {"scheme_id": "PMMVY", "verification_status": "verified"}},
    ]
    store.add_chunks(chunks)
    res = store.similarity_search("farmer crop loss", top_k=1)
    assert len(res) == 1
    assert res[0]["metadata"]["scheme_id"] == "PMFBY"


# 9. Hybrid Retrieval Test
def test_09_hybrid_retrieval():
    engine = LocalEmbeddingEngine(max_features=64)
    store = LocalVectorStore(engine)
    store.add_chunks([
        {"text": "Kisan Credit Card short term loan for agriculture", "metadata": {"scheme_id": "KCC", "verification_status": "verified", "state_or_ut": "all"}},
        {"text": "Mudra loans for micro businesses and enterprises", "metadata": {"scheme_id": "PMMY", "verification_status": "partially_verified", "state_or_ut": "all"}},
    ])
    retriever = HybridRetriever(store)
    hits = retriever.retrieve("Kisan Credit Card loan", top_k=1)
    assert len(hits) == 1
    assert hits[0]["metadata"]["scheme_id"] == "KCC"


# 10. Scheme Filtering Test
def test_10_scheme_filtering():
    repo = SchemeRepository()
    service = SchemeSearchService(repo)
    verified_schemes = service.search_schemes(verification_status="verified")
    assert len(verified_schemes) >= 5
    for s in verified_schemes:
        assert s.verification_status == "verified"


# 11. Eligibility Calculation Test (Eligible vs Not Eligible)
def test_11_eligibility_calculation():
    repo = SchemeRepository()
    scheme = repo.get_scheme_by_id("GOI-CEN-002") # PMJJBY: age 18 to 50
    assert scheme is not None

    # Eligible user (age 30)
    profile_ok = CitizenProfile(age=30, state="Maharashtra")
    report_ok = SchemeEvaluator.evaluate_scheme(scheme, profile_ok)
    assert report_ok.overall_status in ("ELIGIBLE", "NEEDS_VERIFICATION")

    # Ineligible user (age 55 > 50)
    profile_old = CitizenProfile(age=55, state="Maharashtra")
    report_old = SchemeEvaluator.evaluate_scheme(scheme, profile_old)
    assert report_old.overall_status == "NOT_ELIGIBLE"


# 12. Missing Profile Information Handling
def test_12_missing_profile_info():
    repo = SchemeRepository()
    scheme = repo.get_scheme_by_id("GOI-CEN-002")
    profile_empty = CitizenProfile() # No age given
    report = SchemeEvaluator.evaluate_scheme(scheme, profile_empty)
    assert report.overall_status == "NEEDS_VERIFICATION"
    assert "age" in report.missing_fields


# 13. Unverified Scheme Information Handling
def test_13_unverified_scheme_status():
    repo = SchemeRepository()
    scheme = repo.get_scheme_by_id("GOI-CEN-030") # IGNOAPS
    assert scheme is not None
    assert scheme.verification_status == "unverified"
    profile = CitizenProfile(age=65, has_bpl_card=True)
    report = SchemeEvaluator.evaluate_scheme(scheme, profile)
    # Even if age matches, unverified scheme must remain NEEDS_VERIFICATION
    assert report.overall_status == "NEEDS_VERIFICATION"


# 14. Local AI Unavailable (Deterministic Fallback) Test
def test_14_local_ai_unavailable_fallback():
    generator = AnswerGenerator(ollama_url="http://localhost:99999") # Non-existent port
    assert generator.is_ollama_available() is False
    passages = [{
        "text": "PM-KISAN provides INR 6,000 yearly in 3 instalments.",
        "metadata": {"scheme_id": "GOI-CEN-004", "scheme_name": "PM-KISAN", "verification_status": "partially_verified"}
    }]
    ans = generator.generate_answer("How much does PM-KISAN give?", passages, language="en")
    assert "PM-KISAN" in ans["answer"]
    assert ans["engine"] == "deterministic_knowledge_engine"
    assert len(ans["citations"]) == 1


# 15. Empty Database Graceful Handling
def test_15_empty_database():
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        db_path = Path(tmp.name)
        init_database(db_path)
        empty_repo = SchemeRepository(db_path)
        assert empty_repo.count_schemes() == 0
        search = SchemeSearchService(empty_repo)
        assert len(search.search_schemes("farmers")) == 0


# 16. Disallowed / Incorrect Source URL Blocked
def test_16_disallowed_source_url():
    crawler = GovernmentCrawler()
    # Unapproved commercial or scam domain
    res = crawler.fetch_url("https://free-money-schemes.com/apply")
    assert res["success"] is False
    assert res["status_code"] == 403


# 17. English, Hindi, and Marathi Conversations
def test_17_multilingual_conversations():
    engine = LocalEmbeddingEngine(max_features=64)
    store = LocalVectorStore(engine)
    store.add_chunks([
        {"text": "PM-KISAN scheme for farmers", "metadata": {"scheme_id": "GOI-CEN-004", "scheme_name": "PM-KISAN", "verification_status": "verified"}}
    ])
    retriever = HybridRetriever(store)
    generator = AnswerGenerator()
    conv = ConversationManager(retriever, generator)

    p_en = conv.process_message("I am a farmer looking for income support", CitizenProfile(), [], language="en")
    assert "PM-KISAN" in p_en["reply"]

    p_hi = conv.process_message("किसान सहायता", CitizenProfile(), [], language="hi")
    assert "सत्यापन स्थिति" in p_hi["reply"]

    p_mr = conv.process_message("शेतकरी योजना", CitizenProfile(), [], language="mr")
    assert "पडताळणी स्थिती" in p_mr["reply"]


# 18. Citizen Data Deletion Test
def test_18_data_deletion():
    engine = LocalEmbeddingEngine(max_features=32)
    store = LocalVectorStore(engine)
    conv = ConversationManager(HybridRetriever(store), AnswerGenerator())
    profile = CitizenProfile(age=40, state="Bihar", occupation="farmer")
    result = conv.process_message("reset", profile, [], language="en")
    assert result["profile"].age is None
    assert result["profile"].state is None


# 19. Day / Night Mode CSS Generation
def test_19_day_night_mode():
    day_css = get_theme_css(is_dark_mode=False)
    night_css = get_theme_css(is_dark_mode=True)
    assert "#F8FAFC" in day_css
    assert "#0B132B" in night_css


# 20. Admin Review & Source Approval Workflow
def test_20_admin_review_workflow():
    registry = SourceRegistry()
    # Valid gov.in domain
    s1 = registry.add_source("SRC-TEST", "Ministry of Agriculture", "Testing Portal", "https://agricoop.gov.in/test", "Section 1", "eligibility")
    assert s1["is_approved"] is True

    # Invalid non-gov domain
    s2 = registry.add_source("SRC-FAKE", "Private Portal", "Fake Scheme", "https://fakeportal.org/fake", "Section 1", "all")
    assert s2["is_approved"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
