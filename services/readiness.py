"""
Application Readiness Tracker for Civicsaathi.
Calculates personalized document readiness scores separately from scheme eligibility.
Explicitly highlights mandatory, missing, and conditional documents with non-guarantee disclaimers.
"""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from database.models import SchemeRecord, DocumentReadinessReport
from database.repository import SchemeRepository, CitizenDocumentRepository


class ApplicationReadinessTracker:
    def __init__(
        self,
        scheme_repo: Optional[SchemeRepository] = None,
        doc_repo: Optional[CitizenDocumentRepository] = None,
        db_path: Optional[Path] = None,
    ):
        self.scheme_repo = scheme_repo or SchemeRepository(db_path=db_path)
        self.doc_repo = doc_repo or CitizenDocumentRepository(db_path=db_path)

    def evaluate_readiness(
        self,
        scheme: SchemeRecord,
        user_id: Optional[str] = None,
        available_docs: Optional[List[str]] = None,
        language: str = "en",
    ) -> DocumentReadinessReport:
        """
        Evaluates document readiness for a given scheme against citizen's marked documents.
        """
        # Fetch user's marked documents if user_id provided
        user_doc_map = {}
        if user_id:
            user_doc_map = self.doc_repo.get_citizen_documents(user_id)

        user_available_set = set()
        if available_docs:
            user_available_set.update([d.lower().strip() for d in available_docs])
        for doc_name, is_avail in user_doc_map.items():
            if is_avail:
                user_available_set.add(doc_name.lower().strip())

        # Common aliases for matching (e.g., "aadhaar card" -> "aadhaar")
        def is_doc_available(req_str: str) -> bool:
            req_clean = re.sub(r"\[(mandatory|conditional|optional)\]", "", req_str, flags=re.IGNORECASE).lower().strip()
            # Direct match
            if req_clean in user_available_set:
                return True
            # Keyword fuzzy match
            keywords = [
                "aadhaar", "bank account", "passbook", "income certificate", "land record", "khatoni",
                "caste certificate", "ration card", "photo", "voter id", "pan card", "residence certificate"
            ]
            for kw in keywords:
                if kw in req_clean:
                    for u_doc in user_available_set:
                        if kw in u_doc:
                            return True
            return False

        req_list = scheme.required_documents if scheme.required_documents else [
            "[Mandatory] Aadhaar Card",
            "[Mandatory] Bank Account Passbook",
            "[Mandatory] Passport Size Photograph",
        ]

        mandatory_docs = []
        conditional_docs = []
        available_docs_list = []
        missing_mandatory_list = []

        for d in req_list:
            is_conditional = "[conditional]" in d.lower()
            clean_name = re.sub(r"\[(mandatory|conditional|optional)\]", "", d, flags=re.IGNORECASE).strip()

            if is_conditional:
                conditional_docs.append(clean_name)
            else:
                mandatory_docs.append(clean_name)

            if is_doc_available(d):
                available_docs_list.append(clean_name)
            else:
                if not is_conditional:
                    missing_mandatory_list.append(clean_name)

        total_mandatory = len(mandatory_docs)
        available_mandatory_count = total_mandatory - len(missing_mandatory_list)

        if total_mandatory > 0:
            readiness_pct = round((available_mandatory_count / total_mandatory) * 100.0, 1)
        else:
            readiness_pct = 100.0

        if readiness_pct >= 80.0:
            level = "High"
        elif readiness_pct >= 50.0:
            level = "Moderate"
        else:
            level = "Needs Preparation"

        steps = scheme.application_process if scheme.application_process else [
            "1. Keep mandatory identity and income proofs ready.",
            "2. Visit the official online portal or nearest CSC/Bank.",
            "3. Complete Aadhaar e-KYC and submit application form.",
        ]

        disclaimer = (
            "Notice: Document readiness indicates application preparation only and does not guarantee government approval or benefit disbursement. "
            "Official eligibility criteria and administrative verification apply."
        )

        return DocumentReadinessReport(
            scheme_id=scheme.scheme_id,
            scheme_name=f"{scheme.scheme_name} ({', '.join(scheme.alternate_names)})" if scheme.alternate_names else scheme.scheme_name,
            total_required=len(req_list),
            mandatory_count=total_mandatory,
            available_count=len(available_docs_list),
            missing_mandatory=missing_mandatory_list,
            available_documents=available_docs_list,
            conditional_documents=conditional_docs,
            readiness_percentage=readiness_pct,
            readiness_level=level,
            next_steps=steps,
            disclaimer=disclaimer,
        )

    def format_readiness_telegram(self, report: DocumentReadinessReport, language: str = "en") -> str:
        """Renders comprehensive readiness card for Telegram."""
        pct = report.readiness_percentage
        if pct >= 80:
            badge = "🟢 उच्च तैयारी (High)" if language == "hi" else ("🟢 उच्च तयारी (High)" if language == "mr" else "🟢 High Readiness")
        elif pct >= 50:
            badge = "🟡 मध्यम तैयारी (Moderate)" if language == "hi" else ("🟡 मध्यम तयारी (Moderate)" if language == "mr" else "🟡 Moderate Readiness")
        else:
            badge = "🔴 तैयारी आवश्यक (Needs Preparation)" if language == "hi" else ("🔴 तयारी आवश्यक (Needs Preparation)" if language == "mr" else "🔴 Needs Preparation")

        lines = []
        if language == "hi":
            lines.append(f"📋 **आवेदन तैयारी ट्रैकर (Readiness Tracker):**\n*{report.scheme_name}*")
            lines.append("─" * 32)
            lines.append(f"📊 **दस्तावेज़ तैयारी स्तर:** {badge} (**{pct}%**)")
            lines.append(f"• **तैयार दस्तावेज़:** {len(report.available_documents)} / {report.mandatory_count}")

            if report.available_documents:
                lines.append("\n✅ **उपलब्ध दस्तावेज़:**")
                for d in report.available_documents:
                    lines.append(f"  ✓ {d}")

            if report.missing_mandatory:
                lines.append("\n⚠️ **अनुपलब्ध / आवश्यक दस्तावेज़ (Missing):**")
                for d in report.missing_mandatory:
                    lines.append(f"  ✗ {d}")

            if report.conditional_documents:
                lines.append("\n📌 **सशर्त दस्तावेज़ (यदि लागू हो):**")
                for d in report.conditional_documents:
                    lines.append(f"  • {d}")

            lines.append("\n🚀 **अगले आवेदन चरण:**")
            for s in report.next_steps[:3]:
                lines.append(f"• {s}")

            lines.append(f"\n⚠️ *सांविधिक सूचना:* दस्तावेज़ तैयारी केवल आवेदन की पूर्व-तैयारी दर्शाती है और यह सरकारी स्वीकृति या लाभ की गारंटी नहीं देती। अंतिम निर्णय संबंधित विभाग के नियमों पर निर्भर करता है।")
        elif language == "mr":
            lines.append(f"📋 **अर्ज तयारी ट्रॅकर (Readiness Tracker):**\n*{report.scheme_name}*")
            lines.append("─" * 32)
            lines.append(f"📊 **कागदपत्र तयारी पातळी:** {badge} (**{pct}%**)")
            lines.append(f"• **उपलब्ध कागदपत्रे:** {len(report.available_documents)} / {report.mandatory_count}")

            if report.available_documents:
                lines.append("\n✅ **तयार असलेली कागदपत्रे:**")
                for d in report.available_documents:
                    lines.append(f"  ✓ {d}")

            if report.missing_mandatory:
                lines.append("\n⚠️ **अद्याप आवश्यक असलेली कागदपत्रे (Missing):**")
                for d in report.missing_mandatory:
                    lines.append(f"  ✗ {d}")

            if report.conditional_documents:
                lines.append("\n📌 **अटींनुसार लागणारी कागदपत्रे:**")
                for d in report.conditional_documents:
                    lines.append(f"  • {d}")

            lines.append("\n🚀 **पुढील अर्ज प्रक्रिया:**")
            for s in report.next_steps[:3]:
                lines.append(f"• {s}")

            lines.append(f"\n⚠️ *वैधानिक सूचना:* कागदपत्रांची तयारी केवळ प्राथमिक तयारी दर्शवते. ही सरकारी मंजुरी किंवा लाभाची हमी देत नाही. अंतिम निर्णय संबंधित प्रशासकीय नियमांनुसार होईल.")
        else:
            lines.append(f"📋 **Application Readiness Tracker:**\n*{report.scheme_name}*")
            lines.append("─" * 32)
            lines.append(f"📊 **Document Readiness Indicator:** {badge} (**{pct}%**)")
            lines.append(f"• **Ready:** {len(report.available_documents)} of {report.mandatory_count} mandatory proofs")

            if report.available_documents:
                lines.append("\n✅ **Available Documents:**")
                for d in report.available_documents:
                    lines.append(f"  ✓ {d}")

            if report.missing_mandatory:
                lines.append("\n⚠️ **Pending Documents to Arrange:**")
                for d in report.missing_mandatory:
                    lines.append(f"  ✗ {d}")

            if report.conditional_documents:
                lines.append("\n📌 **Conditional Documents (If applicable):**")
                for d in report.conditional_documents:
                    lines.append(f"  • {d}")

            lines.append("\n🚀 **Next Application Steps:**")
            for s in report.next_steps[:3]:
                lines.append(f"• {s}")

            lines.append(f"\n⚠️ *Disclaimer:* Document readiness indicates application preparation only and does not guarantee government approval or disbursement. Official verification by authorities applies.")

        return "\n".join(lines)
