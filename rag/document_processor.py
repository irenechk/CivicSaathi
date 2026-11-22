"""
Document processor for Civicsaathi Knowledge Base.
Transforms canonical SchemeRecords and raw documents into structured RAG chunks with provenance.
"""

from typing import List, Dict, Any
from database.models import SchemeRecord
from rag.chunker import DocumentChunker


class DocumentProcessor:
    def __init__(self, chunker: DocumentChunker = None):
        self.chunker = chunker or DocumentChunker(chunk_size=400, chunk_overlap=80)

    def process_scheme_record(self, scheme: SchemeRecord) -> List[Dict[str, Any]]:
        """
        Processes a SchemeRecord into distinct semantic chunks:
        1. Overview, Objective & Benefits
        2. Eligibility Criteria & Exclusion Rules
        3. Application Process & Required Documents
        4. Official Sources & Provenance Audit
        """
        chunks = []

        alt_names_str = f" ({', '.join(scheme.alternate_names)})" if scheme.alternate_names else ""

        # 1. Overview Chunk
        overview_text = (
            f"Scheme: {scheme.scheme_name}{alt_names_str}\n"
            f"Ministry: {scheme.ministry or 'Central Government'}\n"
            f"Level: {scheme.scheme_level.upper()} | Scope: {scheme.state_or_ut}\n"
            f"Description: {scheme.description}\n"
            f"Objective: {scheme.objective or 'N/A'}\n"
            f"Benefit Type: {', '.join(scheme.benefit_type)}\n"
            f"Benefit Amount: {scheme.benefit_amount or 'Not specified'}\n"
            f"Disbursement Frequency: {scheme.benefit_frequency or 'N/A'}"
        )
        chunks.append({
            "text": overview_text,
            "metadata": {
                "scheme_id": scheme.scheme_id,
                "scheme_name": scheme.scheme_name,
                "alternate_names": scheme.alternate_names,
                "section": "Overview & Benefits",
                "source_url": scheme.official_scheme_url or (scheme.official_source_urls[0] if scheme.official_source_urls else None),
                "verification_status": scheme.verification_status,
                "application_status": scheme.application_status,
                "state_or_ut": scheme.state_or_ut,
                "benefit_types": scheme.benefit_type,
            }
        })

        # 2. Eligibility & Exclusions Chunk
        elig_text = (
            f"Scheme: {scheme.scheme_name}{alt_names_str} Eligibility Criteria\n"
            f"Target Beneficiaries: {', '.join(scheme.target_beneficiaries)}\n"
            f"Age Limit: {scheme.eligibility.age_min or 'Any'} to {scheme.eligibility.age_max or 'Any'}\n"
            f"Income Limit: {f'INR {scheme.eligibility.income_limit}' if scheme.eligibility.income_limit else 'No strict limit specified'}\n"
            f"Eligible Categories: {', '.join(scheme.eligibility.category) if scheme.eligibility.category else 'All'}\n"
            f"Eligible Occupations: {', '.join(scheme.eligibility.occupation) if scheme.eligibility.occupation else 'All'}\n"
            f"Other Conditions: {' '.join(scheme.eligibility.other_conditions) if scheme.eligibility.other_conditions else 'Standard guidelines'}\n"
            f"Exclusions: {' '.join(scheme.exclusion_conditions) if scheme.exclusion_conditions else 'None specified'}"
        )
        chunks.append({
            "text": elig_text,
            "metadata": {
                "scheme_id": scheme.scheme_id,
                "scheme_name": scheme.scheme_name,
                "alternate_names": scheme.alternate_names,
                "section": "Eligibility & Exclusions",
                "source_url": scheme.official_scheme_url or (scheme.official_source_urls[0] if scheme.official_source_urls else None),
                "verification_status": scheme.verification_status,
                "application_status": scheme.application_status,
                "state_or_ut": scheme.state_or_ut,
                "benefit_types": scheme.benefit_type,
            }
        })

        # 3. Application & Documents Chunk
        app_text = (
            f"Scheme: {scheme.scheme_name}{alt_names_str} Application Guidelines\n"
            f"Mode: {scheme.application_mode or 'Online/Offline'}\n"
            f"Official Portal: {scheme.official_application_url or scheme.official_scheme_url or 'See participating bank/CSC'}\n"
            f"Required Documents: {'; '.join(scheme.required_documents) if scheme.required_documents else 'KYC and identity documents'}\n"
            f"Application Steps: {' '.join(scheme.application_process) if scheme.application_process else 'Visit official portal or nearest CSC/Bank branch'}"
        )
        chunks.append({
            "text": app_text,
            "metadata": {
                "scheme_id": scheme.scheme_id,
                "scheme_name": scheme.scheme_name,
                "alternate_names": scheme.alternate_names,
                "section": "Application & Documents",
                "source_url": scheme.official_scheme_url or (scheme.official_source_urls[0] if scheme.official_source_urls else None),
                "verification_status": scheme.verification_status,
                "application_status": scheme.application_status,
                "state_or_ut": scheme.state_or_ut,
                "benefit_types": scheme.benefit_type,
            }
        })

        return chunks
