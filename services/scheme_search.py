"""
Scheme Search Service for Civicsaathi.
Provides multi-attribute search and filtering across the canonical Scheme Knowledge Base.
"""

from typing import List, Dict, Any, Optional
from database.models import SchemeRecord
from database.repository import SchemeRepository


class SchemeSearchService:
    def __init__(self, repository: SchemeRepository):
        self.repository = repository

    def search_schemes(
        self,
        query: Optional[str] = None,
        state: Optional[str] = None,
        ministry: Optional[str] = None,
        benefit_type: Optional[str] = None,
        verification_status: Optional[str] = None,
    ) -> List[SchemeRecord]:
        schemes = self.repository.list_all_schemes()
        filtered = []

        q_lower = query.strip().lower() if query else None

        for s in schemes:
            # 1. State filter
            if state and state.lower() != "all":
                if s.state_or_ut.lower() != "all" and state.lower() not in s.state_or_ut.lower():
                    continue

            # 2. Ministry filter
            if ministry and ministry.lower() != "all":
                if not s.ministry or s.ministry.lower() != ministry.lower():
                    continue

            # 3. Benefit Type filter
            if benefit_type and benefit_type.lower() != "all":
                if benefit_type.lower() not in [b.lower() for b in s.benefit_type]:
                    continue

            # 4. Verification Status filter
            if verification_status and verification_status.lower() != "all":
                if s.verification_status.lower() != verification_status.lower():
                    continue

            # 5. Text search query
            if q_lower:
                match = (
                    q_lower in s.scheme_name.lower() or
                    any(q_lower in alt.lower() for alt in s.alternate_names) or
                    q_lower in s.description.lower() or
                    (s.ministry and q_lower in s.ministry.lower()) or
                    any(q_lower in b.lower() for b in s.target_beneficiaries)
                )
                if not match:
                    continue

            filtered.append(s)

        return filtered
