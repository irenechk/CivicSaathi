"""
Civicsaathi — Independent AI Government Scheme Discovery & Citizen Assistance Platform.
Phase 8 Complete Web Application (Streamlit).
Brand Identity:
- Name: Civicsaathi
- Tagline: From Citizen's Problem to Government Solution — One Guided Journey
- Multilingual: English, Hindi, Marathi
- 10 Functional Modules
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Civicsaathi 🇮🇳 | Government Scheme Assistant",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

from database.connection import init_database
from database.repository import SchemeRepository, CitizenProfileRepository
from database.models import CitizenProfile
from scraper.source_registry import SourceRegistry
from rag.document_processor import DocumentProcessor
from rag.embeddings import LocalEmbeddingEngine
from rag.vector_store import LocalVectorStore
from rag.retriever import HybridRetriever
from rag.answer_generator import AnswerGenerator
from eligibility.evaluator import SchemeEvaluator
from eligibility.explanations import EligibilityExplainer
from chatbot.conversation import ConversationManager
from services.scheme_search import SchemeSearchService
from services.recommendation import RecommendationService
from services.helpline import HelplineService
from services.i18n import SUPPORTED_LANGUAGES, get_text
from ui.components import get_theme_css, render_header, render_scheme_card


# Initialize Databases and Repositories
init_database()
repo = SchemeRepository()
profile_repo = CitizenProfileRepository()
search_service = SchemeSearchService(repo)
recommendation_service = RecommendationService(repo)


# Cache Vector Store and RAG Pipeline
@st.cache_resource
def get_rag_pipeline():
    schemes = repo.list_all_schemes()
    processor = DocumentProcessor()
    chunks = []
    for s in schemes:
        chunks.extend(processor.process_scheme_record(s))

    embedding_engine = LocalEmbeddingEngine()
    vector_store = LocalVectorStore(embedding_engine)
    vector_store.add_chunks(chunks)

    retriever = HybridRetriever(vector_store)
    generator = AnswerGenerator()
    return retriever, generator


retriever, generator = get_rag_pipeline()
chat_manager = ConversationManager(retriever, generator)


# Session State Initialization
if "language" not in st.session_state:
    st.session_state.language = "en"
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "profile" not in st.session_state:
    st.session_state.profile = CitizenProfile(language=st.session_state.language)


# Apply Custom Theme CSS
st.markdown(get_theme_css(st.session_state.dark_mode), unsafe_allow_html=True)


# Sidebar Navigation & Settings
with st.sidebar:
    st.title("🇮🇳 Civicsaathi")
    st.caption("Government Welfare Intelligence")

    # Language Switcher
    lang_options = {"en": "English 🇬🇧", "hi": "हिंदी 🇮🇳", "mr": "मराठी 🇮🇳"}
    selected_lang = st.selectbox(
        "🌐 Language / भाषा / भाषा निवडा",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=list(lang_options.keys()).index(st.session_state.language),
    )
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.session_state.profile.language = selected_lang
        st.rerun()

    # Day / Night Mode Toggle
    dark_toggle = st.toggle("🌙 Night Mode", value=st.session_state.dark_mode)
    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()

    st.markdown("---")

    # Navigation Menu
    pages = [
        "🏠 Home Dashboard",
        "🤖 AI Citizen Assistant",
        "🔍 Explore Schemes",
        "⭐ Personalised Recommendations",
        "⚖️ Eligibility Checker",
        "📄 Document Checklist",
        "📞 Government Helpline",
        "📚 Knowledge Base Explorer",
        "🛠️ Admin Data Management",
        "ℹ️ About and Privacy",
    ]
    page_choice = st.radio("Navigation", pages, label_visibility="collapsed")

    st.markdown("---")
    st.caption("🔒 **Zero-Paid-API Architecture**")
    st.caption("Batch 1 Central Foundation (30 Verified Schemes)")


# ---------------- PAGE 1: HOME DASHBOARD ----------------
if page_choice == "🏠 Home Dashboard":
    render_header(st.session_state.language)
    metrics = repo.get_metrics()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""<div class="metric-box"><div class="metric-number">{metrics['total_schemes']}</div><div class="metric-label">Central Schemes</div></div>""",
            unsafe_allow_html=True,
        )
    with c2:
        verified_count = metrics["status_counts"].get("verified", 0)
        st.markdown(
            f"""<div class="metric-box"><div class="metric-number">{verified_count}</div><div class="metric-label">Strictly Verified</div></div>""",
            unsafe_allow_html=True,
        )
    with c3:
        partial_count = metrics["status_counts"].get("partially_verified", 0)
        st.markdown(
            f"""<div class="metric-box"><div class="metric-number">{partial_count}</div><div class="metric-label">Partially Verified</div></div>""",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            """<div class="metric-box"><div class="metric-number">25</div><div class="metric-label">Official Sources</div></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🎯 Key Welfare Pillars (Batch 1)")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown("#### 🌾 Agriculture & Farmers")
        st.markdown("- **PM-KISAN:** ₹6,000/yr direct income support\n- **KCC:** 7% short-term credit with 3% incentive\n- **PMFBY:** Subsidized seasonal crop insurance")
    with p2:
        st.markdown("#### 🛡️ Insurance & Social Security")
        st.markdown("- **PMJJBY:** ₹2 Lakh life cover for ₹436/yr\n- **PMSBY:** ₹2 Lakh accident cover for ₹20/yr\n- **Atal Pension Yojana:** Guaranteed old-age pension")
    with p3:
        st.markdown("#### 👩 Women & Micro-Enterprises")
        st.markdown("- **PMMVY:** ₹5,000 / ₹6,000 maternity benefit\n- **Mudra (PMMY):** Collateral-free loans up to ₹20 Lakh\n- **PM Vishwakarma:** Artisans toolkit + enterprise credit")

    st.markdown("---")
    st.subheader("🚀 Quick Scheme Search")
    quick_q = st.text_input("Search government benefits by keywords, category, or profession:", placeholder="e.g. crop loan, pregnancy benefit, life insurance, student loan")
    if quick_q:
        results = search_service.search_schemes(query=quick_q)
        st.caption(f"Found {len(results)} matching schemes:")
        for res in results[:5]:
            render_scheme_card(res.model_dump(), st.session_state.language)


# ---------------- PAGE 2: AI CITIZEN ASSISTANT ----------------
elif page_choice == "🤖 AI Citizen Assistant":
    render_header(st.session_state.language)
    st.subheader("🤖 Conversational Assistant")
    st.caption("Ask questions about government schemes in English, Hindi, or Marathi. All answers are grounded in verified government documents.")

    # Display Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("citations"):
                with st.expander("📌 Verified Government Citations"):
                    for c in msg["citations"]:
                        st.markdown(f"- **{c['scheme_name']}** ({c['scheme_id']}) — [{c['source_url']}]({c['source_url']}) — *{c['verification_status']}*")

    # Chat Input
    user_input = st.chat_input("Type your question or problem here (e.g., 'I am a 25 year old farmer from Maharashtra, what benefits can I get?'):")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        response_dict = chat_manager.process_message(
            user_message=user_input,
            profile=st.session_state.profile,
            chat_history=st.session_state.chat_history,
            language=st.session_state.language,
        )

        st.session_state.profile = response_dict["profile"]

        with st.chat_message("assistant"):
            st.markdown(response_dict["reply"])
            if response_dict.get("citations"):
                with st.expander("📌 Verified Government Citations"):
                    for c in response_dict["citations"]:
                        st.markdown(f"- **{c['scheme_name']}** ({c['scheme_id']}) — [{c['source_url']}]({c['source_url']}) — *{c['verification_status']}*")

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response_dict["reply"],
            "citations": response_dict.get("citations", []),
        })


# ---------------- PAGE 3: EXPLORE SCHEMES ----------------
elif page_choice == "🔍 Explore Schemes":
    st.title("🔍 Explore Central Government Schemes")
    st.caption("Browse 30 structured Central Sector and Centrally Sponsored schemes across ministries.")

    f1, f2, f3 = st.columns(3)
    with f1:
        ministry_filter = st.selectbox(
            "Filter by Ministry",
            ["All"] + sorted(list(set([s.ministry for s in repo.list_all_schemes() if s.ministry]))),
        )
    with f2:
        benefit_filter = st.selectbox(
            "Filter by Benefit Type",
            ["All", "cash", "loan", "insurance", "subsidy", "scholarship", "training", "in_kind", "pension"],
        )
    with f3:
        status_filter = st.selectbox(
            "Verification Status",
            ["All", "verified", "partially_verified", "unverified"],
        )

    search_query = st.text_input("Keyword filter:", placeholder="Search by name, acronym, or eligibility...")

    matched_schemes = search_service.search_schemes(
        query=search_query if search_query else None,
        ministry=ministry_filter if ministry_filter != "All" else None,
        benefit_type=benefit_filter if benefit_filter != "All" else None,
        verification_status=status_filter if status_filter != "All" else None,
    )

    st.write(f"Showing **{len(matched_schemes)}** schemes:")
    for s in matched_schemes:
        render_scheme_card(s.model_dump(), st.session_state.language)


# ---------------- PAGE 4: PERSONALISED RECOMMENDATIONS ----------------
elif page_choice == "⭐ Personalised Recommendations":
    st.title("⭐ Personalised Scheme Recommendations")
    st.caption("Tell Civicsaathi about your situation to receive ranked scheme matches based on deterministic rule evaluation.")

    with st.expander("📝 Fill / Edit Your Citizen Profile", expanded=True):
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st_val = st.text_input("State / Union Territory", value=st.session_state.profile.state or "Maharashtra")
            age_val = st.number_input("Age (Years)", min_value=1, max_value=110, value=st.session_state.profile.age or 28)
            gender_val = st.selectbox("Gender", ["female", "male", "other"], index=0 if st.session_state.profile.gender == "female" else 1)
        with p_col2:
            occ_val = st.selectbox(
                "Primary Occupation",
                ["farmer", "cultivator", "artisan", "street_vendor", "student", "unorganized_worker", "employed", "self_employed", "homemaker"],
                index=0,
            )
            income_val = st.number_input("Annual Family Income (INR)", min_value=0, max_value=10000000, value=int(st.session_state.profile.annual_family_income or 200000), step=25000)
            cat_val = st.selectbox("Category", ["General", "OBC", "SC", "ST", "EBC", "Minority"])

        if st.button("Update Profile & Recalculate"):
            st.session_state.profile.state = st_val
            st.session_state.profile.age = age_val
            st.session_state.profile.gender = gender_val
            st.session_state.profile.occupation = occ_val
            st.session_state.profile.annual_family_income = float(income_val)
            st.session_state.profile.category = cat_val
            profile_repo.save_profile(st.session_state.profile)
            st.success("Profile saved securely in local SQLite.")

    recs = recommendation_service.get_recommendations_for_profile(st.session_state.profile)

    st.markdown("### 🏆 Top Recommended Schemes for You")
    if not recs:
        st.info("No recommendations found. Adjust profile filters.")
    for report in recs:
        scheme_obj = repo.get_scheme_by_id(report.scheme_id)
        if not scheme_obj:
            continue
        status_color = "#166534" if report.overall_status == "ELIGIBLE" else "#854D0E"
        st.markdown(
            f"""
            <div class="scheme-card" style="border-left: 5px solid {status_color};">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-size: 1.15rem; font-weight:700;">{report.scheme_name}</span>
                    <span class="badge" style="background-color: {status_color}; color:#FFF;">{report.overall_status}</span>
                </div>
                <p style="margin: 0.5rem 0; font-size:0.9rem;">{scheme_obj.description}</p>
                <div style="font-size:0.85rem; color:#475569;"><strong>Benefit:</strong> {report.benefit_summary}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(f"Inspect Evaluation Rules for {report.scheme_name}"):
            explanation_text = EligibilityExplainer.explain_report(report, st.session_state.language)
            st.markdown(explanation_text)


# ---------------- PAGE 5: ELIGIBILITY CHECKER ----------------
elif page_choice == "⚖️ Eligibility Checker":
    st.title("⚖️ Deterministic Eligibility Evaluator")
    st.caption("AI never makes final eligibility determinations. Inspect exact rules, thresholds, and evaluations.")

    all_schemes = repo.list_all_schemes()
    scheme_names = {s.scheme_id: f"{s.scheme_id} - {s.scheme_name}" for s in all_schemes}
    selected_id = st.selectbox("Select Scheme to inspect:", list(scheme_names.keys()), format_func=lambda x: scheme_names[x])

    chosen_scheme = repo.get_scheme_by_id(selected_id)
    if chosen_scheme:
        st.subheader(chosen_scheme.scheme_name)
        st.markdown(f"**Verification Status:** `{chosen_scheme.verification_status}` | **Confidence:** `{chosen_scheme.research_confidence}`")

        evaluator = SchemeEvaluator()
        report = evaluator.evaluate_scheme(chosen_scheme, st.session_state.profile)

        explanation = EligibilityExplainer.explain_report(report, st.session_state.language)
        st.markdown(explanation)


# ---------------- PAGE 6: DOCUMENT CHECKLIST ----------------
elif page_choice == "📄 Document Checklist":
    st.title("📄 Required Documents Generator")
    st.caption("View verified document requirements and checklists before applying.")

    all_schemes = repo.list_all_schemes()
    scheme_names = {s.scheme_id: f"{s.scheme_id} - {s.scheme_name}" for s in all_schemes}
    selected_id = st.selectbox("Select Scheme for Document Checklist:", list(scheme_names.keys()), format_func=lambda x: scheme_names[x])

    chosen_scheme = repo.get_scheme_by_id(selected_id)
    if chosen_scheme:
        st.subheader(f"Documents for: {chosen_scheme.scheme_name}")
        if chosen_scheme.required_documents:
            for doc in chosen_scheme.required_documents:
                st.markdown(f"- ✅ **{doc}**")
        else:
            st.info("No scheme-specific document list extracted yet in Batch 1. Standard KYC (Aadhaar, Bank Passbook) typically applies.")


# ---------------- PAGE 7: GOVERNMENT HELPLINE ----------------
elif page_choice == "📞 Government Helpline":
    st.title("📞 Official Government Helplines")
    st.caption("Verified national and state toll-free helplines across India.")

    categories = ["All", "Emergency & Safety", "Agriculture & Farmers", "Women & Child", "Healthcare", "Senior Citizens", "Consumer & Public Services", "Financial Inclusion"]
    cat_pick = st.selectbox("Filter Helpline Category:", categories)

    helplines = HelplineService.get_helplines(cat_pick)
    for h in helplines:
        st.markdown(
            f"""
            <div class="scheme-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="margin:0; font-size:1.15rem;">{h['name']}</h4>
                    <span style="font-size:1.2rem; font-weight:800; color:#FF9933; background-color:rgba(255,153,51,0.1); padding:0.2rem 0.6rem; border-radius:6px;">{h['number']}</span>
                </div>
                <p style="margin:0.4rem 0 0.2rem 0; font-size:0.85rem; color:#64748B;">Category: <strong>{h['category']}</strong> | Scope: {h['scope']} | Timing: {h['timing']}</p>
                <p style="margin:0; font-size:0.9rem;">{h['description']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------- PAGE 8: KNOWLEDGE BASE EXPLORER ----------------
elif page_choice == "📚 Knowledge Base Explorer":
    st.title("📚 Scheme Knowledge Base Explorer")
    st.caption("Inspect canonical JSON schemas, data dictionary, and provenance metadata.")

    all_schemes = repo.list_all_schemes()
    scheme_names = {s.scheme_id: f"{s.scheme_id} - {s.scheme_name}" for s in all_schemes}
    selected_id = st.selectbox("Inspect Full Scheme Record:", list(scheme_names.keys()), format_func=lambda x: scheme_names[x])

    chosen_scheme = repo.get_scheme_by_id(selected_id)
    if chosen_scheme:
        st.json(chosen_scheme.model_dump())


# ---------------- PAGE 9: ADMIN DATA MANAGEMENT ----------------
elif page_choice == "🛠️ Admin Data Management":
    st.title("🛠️ Admin Data & Crawl Management")
    st.caption("Manage government source URLs, review crawled documents, and audit coverage.")

    registry = SourceRegistry()
    sources = registry.load_sources()

    st.subheader(f"Approved Government Sources ({len(sources)})")
    df_sources = pd.DataFrame(sources)
    st.dataframe(df_sources[["source_ref", "publisher", "document_or_page_title", "exact_url"]], use_container_width=True)

    with st.expander("➕ Add & Approve New Source URL"):
        s_ref = st.text_input("Source Ref (e.g. SRC-26)")
        s_pub = st.text_input("Publisher (Ministry / Department)")
        s_title = st.text_input("Document or Page Title")
        s_url = st.text_input("Exact Government URL (must be *.gov.in or *.nic.in)")
        s_sec = st.text_input("Relevant Section")
        s_fields = st.text_input("Fields Supported")

        if st.button("Add Source"):
            if s_url and registry.is_permitted_url(s_url):
                registry.add_source(s_ref, s_pub, s_title, s_url, s_sec, s_fields)
                st.success(f"Source {s_ref} successfully approved and added.")
            else:
                st.error("Invalid URL. Domain must be an approved official Indian Government domain (*.gov.in / *.nic.in).")


# ---------------- PAGE 10: ABOUT AND PRIVACY ----------------
elif page_choice == "ℹ️ About and Privacy":
    st.title("ℹ️ About Civicsaathi & Citizen Privacy Charter")
    st.markdown(
        """
        ### 🏛️ Mission & Architecture
        Civicsaathi is built to bridge the gap between Indian citizens and government welfare assistance.
        
        **Core Principles:**
        - **100% Data Sovereignty:** Zero dependency on paid third-party scheme APIs or paid LLM APIs for core retrieval.
        - **Deterministic Eligibility:** Algorithms evaluate verifiable official thresholds. AI never promises approvals.
        - **Zero Surveillance:** We never ask for, collect, or store Aadhaar numbers, biometric data, OTPs, or bank passwords.
        - **Full Provenance:** Every fact links directly to primary sources (*myscheme.gov.in, pib.gov.in, scholarships.gov.in*).
        - **Data Deletion:** Citizens retain full ownership of their data and can clear their profile anytime.
        """
    )
    if st.button("🗑️ Delete My Profile Data Now"):
        st.session_state.profile = CitizenProfile(language=st.session_state.language)
        st.session_state.chat_history = []
        st.success("Your profile and chat history have been erased from memory.")
