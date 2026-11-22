"""
Scheme Recommendation Service for Civicsaathi.
Evaluates all canonical schemes against a citizen profile and generates ranked recommendations.
"""

from typing import List, Dict, Any, Optional
from database.models import SchemeRecord, CitizenProfile, SchemeEligibilityReport
from database.repository import SchemeRepository
from eligibility.evaluator import SchemeEvaluator


class RecommendationService:
    def __init__(self, repository: Optional[SchemeRepository] = None):
        self.repository = repository or SchemeRepository()
        self.evaluator = SchemeEvaluator()

    def get_recommendations_for_profile(self, profile: CitizenProfile) -> List[SchemeEligibilityReport]:
        schemes = self.repository.list_all_schemes()
        reports = []

        for scheme in schemes:
            report = self.evaluator.evaluate_scheme(scheme, profile)
            reports.append(report)

        # Priority Ranking:
        # 1. ELIGIBLE (High priority)
        # 2. NEEDS_VERIFICATION (Medium priority)
        # 3. NOT_ELIGIBLE (Excluded from top recommendations)
        eligible = [r for r in reports if r.overall_status == "ELIGIBLE"]
        needs_verif = [r for r in reports if r.overall_status == "NEEDS_VERIFICATION"]

        # Sort verified before partially_verified
        return eligible + needs_verif

    def get_recommendations(self, profile: CitizenProfile) -> Dict[str, Any]:
        """Convenience method returning categorized recommendation dictionaries."""
        all_recs = self.get_recommendations_for_profile(profile)
        eligible = [r for r in all_recs if r.overall_status == "ELIGIBLE"]
        needs_verif = [r for r in all_recs if r.overall_status == "NEEDS_VERIFICATION"]
        return {
            "eligible": eligible,
            "needs_verification": needs_verif,
            "all_ranked": all_recs,
        }
