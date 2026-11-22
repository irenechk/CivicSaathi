# Civicsaathi 🇮🇳 — Sovereign Government Scheme Intelligence Platform

> **From Citizen's Problem to Government Solution — One Guided Journey**

Civicsaathi is an independent, AI-powered government scheme discovery and citizen assistance platform built for Indian citizens. It operates with **zero dependency on third-party scheme APIs or paid AI APIs** for its core data pipeline, knowledge base, retrieval system, and eligibility engine.

---

## 🏛️ System Architecture

Civicsaathi features a clean, modular architecture:

```text
civicsaathi/
├── app.py                      # Streamlit 10-page citizen and admin platform
├── bot.py                      # Telegram bot daemon (Phase 1 & 2 multilingual bot)
├── config.py                   # Pydantic & python-dotenv secure configuration
├── requirements.txt            # Python dependencies (Streamlit, aiogram, pypdf, etc.)
├── run.sh                      # One-click launch script
├── .env / .env.example         # Environment credentials (gitignored)
├── .gitignore                  # Git privacy rules
│
├── data/
│   ├── raw/                    # Batch 1 Central JSONL, CSVs, and Research Gaps
│   │   ├── schemes_master.jsonl   # 30 canonical Central schemes
│   │   ├── schemes_summary.csv    # Spreadsheet audit table
│   │   ├── sources_registry.csv   # 25 verified official Government sources
│   │   └── research_gaps.csv      # 43 named schemes queued for Batch 1B
│   ├── processed/              # Processed chunks & embeddings cache
│   ├── schemes/                # Structured canonical JSON records
│   ├── sources/                # Source logs & crawl manifests
│   ├── reports/                # Eligibility evaluation audit reports
│   ├── documents/              # Stored official PDF guidelines
│   └── civicsaathi.db          # Local SQLite knowledge base & user preferences
│
├── scraper/                    # Sovereign Government data collection
│   ├── source_registry.py      # Approved *.gov.in / *.nic.in domain registry
│   ├── crawler.py              # Polite, rate-limited HTTP crawler
│   ├── html_extractor.py       # HTML section, headings, and PDF link extractor
│   ├── pdf_extractor.py        # Local PDF text extraction (pypdf)
│   ├── normalizer.py           # Text cleaning, currency and tag normalization
│   ├── deduplicator.py         # Title and acronym duplicate/merge detector
│   └── validator.py            # Canonical 30-field schema validator
│
├── database/                   # Storage & Persistence Layer
│   ├── models.py               # Canonical 30-field Scheme & Profile Pydantic schemas
│   ├── connection.py           # SQLite connection & schema initialization
│   ├── repository.py           # High-level Scheme & Profile repositories
│   └── ingest_raw_data.py      # Pipeline script for Batch 1 ingestion
│
├── rag/                        # 100% Local RAG Retrieval Pipeline
│   ├── document_processor.py   # Multi-section semantic chunking with provenance
│   ├── chunker.py              # Paragraph and sliding-window chunker
│   ├── embeddings.py           # Local TF-IDF + BM25 Sublinear N-gram vectorizer
│   ├── vector_store.py         # Local vector store with metadata filtering
│   ├── retriever.py            # Hybrid semantic + lexical retriever
│   └── answer_generator.py     # Multilingual synthesizer with source citations
│
├── eligibility/                # Deterministic Rule Engine
│   ├── rule_engine.py          # Predicate evaluator (eq, neq, lte, gte, in, not_in)
│   ├── evaluator.py            # ELIGIBLE / NOT_ELIGIBLE / NEEDS_VERIFICATION classifier
│   └── explanations.py         # Localized citizen explanations (EN, HI, MR)
│
├── chatbot/                    # Conversational Assistant
│   ├── profile_extractor.py    # Non-intrusive profile attribute extractor
│   ├── question_manager.py     # Progressive questioning flow (No Aadhaar/OTPs)
│   ├── conversation.py         # Multi-turn stateful dialogue manager
│   └── response_builder.py     # Friendly, respectful, localized response formatter
│
├── services/                   # Business Services
│   ├── scheme_search.py        # Multi-attribute filtering (state, ministry, status)
│   ├── recommendation.py       # Ranked profile-to-scheme matching
│   └── helpline.py             # Verified national toll-free helplines (112, Kisan 1800-180-1551, etc.)
│
├── ui/                         # User Interface
│   ├── components.py           # Theme CSS (Day/Night mode, Deep Navy, Saffron, Teal), Cards
│   └── pages/                  # Page definitions
│
└── tests/                      # Automated Verification Test Suites
    ├── test_civicsaathi.py     # Telegram bot test suite (7 tests)
    └── test_platform_full.py   # Comprehensive platform test suite (20 tests)
```

---

## 📊 Batch 1 Central Scheme Knowledge Base

- **Individually Identified Central Schemes:** 73 (30 structured in JSONL + 43 queued in `research_gaps.csv`).
- **Verified Schemes (5):** PMMVY, PMJJBY, PMSBY, PMFBY, KCC.
- **Partially Verified (24):** PM-KISAN, PMAY-U 2.0, PM SVANidhi, PM Vishwakarma, APY, PMAY-G, PM Surya Ghar, PMGKAY, MGNREGA, AB-PMJAY, PMJDY, SSY, PMKVY, NAVYA, NSP scholarships, Stand-Up India, etc.
- **Unverified (1):** IGNOAPS Central baseline (preserved unverified pending primary NSAP guidelines).
- **State Quarantine:** All 28 states quarantined from Central records; queued for Batches 2+ starting with Maharashtra.

---

## 🚀 Setup & Launch Instructions

### 1. Environment Setup
```bash
cd /Users/aashikapandey/.gemini/antigravity/scratch/civicsaathi
source .venv/bin/activate
```

### 2. Ingest Batch 1 Data
```bash
python3 database/ingest_raw_data.py
```

### 3. Run Automated Tests (27 Tests)
```bash
python3 -m pytest tests/test_platform_full.py tests/test_civicsaathi.py -v
```

### 4. Launch the Web Platform (Streamlit)
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 5. Launch the Telegram Bot
```bash
python3 bot.py
```

---

## 🔒 Citizen Privacy Charter

- **No Third-Party AI API Dependency:** Core search, embeddings, vector retrieval, and eligibility evaluation run 100% locally.
- **Zero Sensitive Data Collection:** We **never** ask for, collect, or store Aadhaar numbers, biometric credentials, OTPs, or bank passwords.
- **Data Deletion:** Citizens can delete their profile anytime by typing `reset` in chat or clicking **Delete My Profile Data** in the web app.
