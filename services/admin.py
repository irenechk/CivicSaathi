"""
Admin Verification Service for Civicsaathi.
Provides administrative controls to:
- Review extracted schemes & verify official sources.
- Explicitly approve or reject schemes (unverified scraped data never auto-promotes).
- Update eligibility rules with version archiving.
- Flag outdated or conflicting information.
- Inspect source coverage metrics & scraper error logs.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from database.repository import SchemeRepository
from database.models import SchemeRecord


class AdminVerificationService:
    def __init__(self, repository: Optional[SchemeRepository] = None, db_path: Optional[Path] = None):
        self.repository = repository or SchemeRepository(db_path=db_path)

    def get_pending_schemes(self) -> List[Dict[str, Any]]:
        """Lists schemes needing verification review."""
        all_schemes = self.repository.list_all_schemes()
        pending = []
        for s in all_schemes:
            if s.verification_status in ("unverified", "partially_verified", "outdated", "conflicting"):
                pending.append({
                    "scheme_id": s.scheme_id,
                    "scheme_name": s.scheme_name,
                    "verification_status": s.verification_status,
                    "research_confidence": s.research_confidence,
                    "official_source_urls": s.official_source_urls,
                    "guidelines_document_urls": s.guidelines_document_urls,
                    "data_gaps": s.data_gaps,
                })
        return pending

    def verify_and_approve_scheme(
        self,
        scheme_id: str,
        admin_id: str = "admin",
        verified_date: str = "2026-11-22",
        admin_notes: Optional[str] = None,
    ) -> bool:
        """
        Explicitly promotes a scheme to 'verified' after human admin review.
        Enforces: Scraped data never auto-promotes without admin action.
        """
        scheme = self.repository.get_scheme_by_id(scheme_id)
        if not scheme:
            return False

        # Archive version before updating
        self.repository.archive_scheme_version(
            scheme_id=scheme_id,
            version_tag="v_approved",
            change_notes=f"Admin approval by {admin_id}: {admin_notes or 'Official sources verified'}",
            source_doc=scheme.guidelines_document_urls[0] if scheme.guidelines_document_urls else None,
            created_by=admin_id,
        )

        scheme.verification_status = "verified"
        scheme.research_confidence = "high"
        scheme.research_verified_date = verified_date
        if admin_notes:
            scheme.source_notes.append(f"Admin Approval ({admin_id}): {admin_notes}")
        self.repository.upsert_scheme(scheme)
        return True

    def reject_scheme(self, scheme_id: str, reason: str, admin_id: str = "admin") -> bool:
        """Rejects unverified or fraudulent scraped scheme record."""
        scheme = self.repository.get_scheme_by_id(scheme_id)
        if not scheme:
            return False
        scheme.verification_status = "unverified"
        scheme.application_status = "DISCONTINUED_CONFIRMED"
        scheme.source_notes.append(f"Admin Rejection by {admin_id}: {reason}")
        self.repository.upsert_scheme(scheme)
        self.repository.flag_scheme_for_review(scheme_id, "rejected", reason, {"admin_id": admin_id})
        return True

    def update_eligibility_rules(
        self,
        scheme_id: str,
        new_eligibility: Dict[str, Any],
        admin_id: str = "admin",
        change_reason: str = "Policy guidelines update",
    ) -> bool:
        """Updates eligibility rules with automatic historical archiving."""
        scheme = self.repository.get_scheme_by_id(scheme_id)
        if not scheme:
            return False

        # Archive historical eligibility
        self.repository.archive_scheme_version(
            scheme_id=scheme_id,
            version_tag="v_rule_update",
            change_notes=f"Rules updated by {admin_id}: {change_reason}",
            source_doc=scheme.guidelines_document_urls[0] if scheme.guidelines_document_urls else None,
            created_by=admin_id,
        )

        for k, v in new_eligibility.items():
            if hasattr(scheme.eligibility, k):
                setattr(scheme.eligibility, k, v)

        self.repository.upsert_scheme(scheme)
        return True

    def flag_outdated_or_conflicting(
        self,
        scheme_id: str,
        flag_type: str,  # 'outdated' or 'conflicting'
        reason: str,
        admin_id: str = "admin",
    ) -> int:
        """Flags scheme for review and marks status as outdated/conflicting."""
        self.repository.update_scheme_verification(scheme_id, flag_type)
        return self.repository.flag_scheme_for_review(
            scheme_id=scheme_id,
            flag_type=flag_type,
            reason=reason,
            details={"flagged_by": admin_id},
        )

    def get_source_coverage(self) -> Dict[str, Any]:
        """Provides high-level audit metrics on scheme provenance and verification status."""
        metrics = self.repository.get_metrics()
        all_schemes = self.repository.list_all_schemes()
        total_sources = sum(len(s.official_source_urls) for s in all_schemes)
        total_guidelines = sum(len(s.guidelines_document_urls) for s in all_schemes)

        return {
            "total_schemes": metrics["total_schemes"],
            "status_breakdown": metrics["status_counts"],
            "ministries_covered": len(metrics["ministry_counts"]),
            "total_official_sources_registered": total_sources,
            "total_guideline_documents": total_guidelines,
            "pending_review_count": sum(1 for s in all_schemes if s.verification_status != "verified"),
        }

    def get_scraper_and_review_logs(self) -> List[Dict[str, Any]]:
        """Returns all review flags and issues needing attention."""
        return self.repository.get_admin_flags(status="pending")

    def format_admin_summary_telegram(self) -> str:
        """Renders executive admin overview for Telegram."""
        cov = self.get_source_coverage()
        flags = self.get_scraper_and_review_logs()

        lines = [
            "🛡️ **Civicsaathi Admin Verification Console**",
            "─" * 32,
            f"📊 **Scheme Corpus:** {cov['total_schemes']} Central Schemes",
            f"• **Verified:** {cov['status_breakdown'].get('verified', 0)}",
            f"• **Partially Verified:** {cov['status_breakdown'].get('partially_verified', 0)}",
            f"• **Unverified / Under Review:** {cov['status_breakdown'].get('unverified', 0)}",
            f"• **Outdated / Flagged:** {cov['status_breakdown'].get('outdated', 0) + cov['status_breakdown'].get('conflicting', 0)}",
            f"• **Ministries Covered:** {cov['ministries_covered']}",
            f"• **Registered Sources:** {cov['total_official_sources_registered']} URLs | {cov['total_guideline_documents']} Guidelines",
            f"\n⚠️ **Active Flags for Review:** {len(flags)}",
        ]

        if flags:
            for f in flags[:3]:
                lines.append(f"• Flag #{f['flag_id']} [{f['flag_type'].upper()}] {f['scheme_id']}: {f['reason']}")

        lines.append("\n💡 *To verify a scheme: `/admin approve <scheme_id>`*")
        lines.append("💡 *To flag outdated: `/admin flag <scheme_id> <reason>`*")
        return "\n".join(lines)
