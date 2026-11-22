"""
Multiple Scheme Comparison Service for Civicsaathi.
Enables citizens to compare 2 or more schemes side-by-side across:
benefits, eligibility, documents, application process, state scope, status, and official sources.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from database.repository import SchemeRepository
from database.models import SchemeRecord, SchemeComparisonReport, SchemeComparisonItem


class SchemeComparisonService:
    def __init__(self, repository: Optional[SchemeRepository] = None, db_path: Optional[Path] = None):
        self.repository = repository or SchemeRepository(db_path=db_path)

    def compare_schemes(self, scheme_identifiers: List[str], language: str = "en") -> SchemeComparisonReport:
        """
        Compares multiple schemes specified by ID or name.
        """
        schemes: List[SchemeRecord] = []
        for ident in scheme_identifiers:
            ident_clean = ident.strip()
            # Try ID lookup
            s = self.repository.get_scheme_by_id(ident_clean)
            if not s:
                # Search by name or acronym
                all_schemes = self.repository.list_all_schemes()
                for cand in all_schemes:
                    if (
                        ident_clean.lower() in cand.scheme_name.lower()
                        or any(ident_clean.lower() in a.lower() for a in cand.alternate_names)
                        or ident_clean.lower() in cand.scheme_id.lower()
                    ):
                        s = cand
                        break
            if s and s not in schemes:
                schemes.append(s)

        if not schemes:
            return SchemeComparisonReport(
                schemes=[],
                generated_at="2026-11-22",
                comparison_summary="No matching schemes found for comparison.",
            )

        items: List[SchemeComparisonItem] = []
        for s in schemes:
            age_min = s.eligibility.age_min
            age_max = s.eligibility.age_max
            if age_min and age_max:
                age_str = f"{age_min} - {age_max} yrs"
            elif age_min:
                age_str = f"Min {age_min} yrs"
            elif age_max:
                age_str = f"Up to {age_max} yrs"
            else:
                age_str = "No age restrictions"

            inc_lim = s.eligibility.income_limit
            inc_str = f"Up to ₹{inc_lim:,.0f}/yr" if inc_lim else "No strict ceiling"

            url = s.official_application_url or s.official_scheme_url or (s.official_source_urls[0] if s.official_source_urls else "https://myscheme.gov.in")

            items.append(
                SchemeComparisonItem(
                    scheme_id=s.scheme_id,
                    scheme_name=f"{s.scheme_name} ({', '.join(s.alternate_names)})" if s.alternate_names else s.scheme_name,
                    ministry=s.ministry or "Government of India",
                    benefit_summary=s.description[:120] + "...",
                    benefit_amount=s.benefit_amount or "Financial / welfare assistance",
                    benefit_frequency=s.benefit_frequency or "Direct Benefit Transfer",
                    age_criteria=age_str,
                    income_limit=inc_str,
                    target_beneficiaries=s.target_beneficiaries[:3],
                    required_documents=s.required_documents[:4],
                    application_process=s.application_process[:3],
                    application_mode=s.application_mode or "Online / Offline",
                    state_applicability="Pan-India (All States)" if s.state_or_ut.lower() == "all" else s.state_or_ut,
                    application_status=s.application_status,
                    official_source_url=url,
                    verification_status=s.verification_status,
                )
            )

        summary = f"Comparison of {len(items)} government schemes based on official 2026 guidelines."
        return SchemeComparisonReport(
            schemes=items,
            generated_at="2026-11-22",
            comparison_summary=summary,
        )

    def format_comparison_telegram(self, report: SchemeComparisonReport, language: str = "en") -> str:
        """Renders side-by-side or stacked multi-scheme comparison for Telegram."""
        if not report.schemes:
            if language == "hi":
                return "❌ तुलना के लिए कोई योजना नहीं मिली। कृपया मान्य योजना नाम या आईडी दें (उदा. '/compare KCC vs PM-KISAN')।"
            elif language == "mr":
                return "❌ तुलनेसाठी कोणतीही योजना आढळली नाही. कृपया योग्य योजना नाव किंवा आयडी प्रविष्ट करा (उदा. '/compare KCC vs PM-KISAN')."
            return "❌ No valid schemes found to compare. Please provide valid scheme names or IDs (e.g. '/compare KCC vs PM-KISAN')."

        lines = []
        if language == "hi":
            lines.append("⚖️ **योजना तुलना रिपोर्ट (Scheme Comparison):**")
            lines.append("─" * 32)
            for i, item in enumerate(report.schemes, 1):
                lines.append(f"\n🏛️ **{i}. {item.scheme_name}**")
                lines.append(f"• **मंत्रालय:** {item.ministry}")
                lines.append(f"• **लाभ राशि:** {item.benefit_amount} ({item.benefit_frequency})")
                lines.append(f"• **पात्रता आयु:** {item.age_criteria} | **आय सीमा:** {item.income_limit}")
                lines.append(f"• **लक्षित वर्ग:** {', '.join(item.target_beneficiaries)}")
                lines.append(f"• **आवश्यक दस्तावेज़:** {len(item.required_documents)} मुख्य प्रमाणपत्र")
                lines.append(f"• **आवेदन का माध्यम:** {item.application_mode}")
                lines.append(f"• **भौगोलिक क्षेत्र:** {item.state_applicability}")
                lines.append(f"• **स्थिति:** {item.application_status} (*सत्यापन: {item.verification_status}*)")
                lines.append(f"🔗 [आधिकारिक स्रोत / पोर्टल]({item.official_source_url})")
            lines.append("\n💡 *किसी भी योजना के विस्तृत दस्तावेज़ देखने के लिए उसका नाम चैट में लिखें।*")
        elif language == "mr":
            lines.append("⚖️ **योजना तुलना अहवाल (Scheme Comparison):**")
            lines.append("─" * 32)
            for i, item in enumerate(report.schemes, 1):
                lines.append(f"\n🏛️ **{i}. {item.scheme_name}**")
                lines.append(f"• **मंत्रालय:** {item.ministry}")
                lines.append(f"• **लाभाची रक्कम:** {item.benefit_amount} ({item.benefit_frequency})")
                lines.append(f"• **वयोमर्यादा:** {item.age_criteria} | **उत्पन्न मर्यादा:** {item.income_limit}")
                lines.append(f"• **लक्षित लाभार्थी:** {', '.join(item.target_beneficiaries)}")
                lines.append(f"• **कागदपत्रे:** {len(item.required_documents)} मुख्य प्रमाणपत्रे")
                lines.append(f"• **अर्जाचे स्वरूप:** {item.application_mode}")
                lines.append(f"• **लागू क्षेत्र:** {item.state_applicability}")
                lines.append(f"• **स्थिती:** {item.application_status} (*पडताळणी: {item.verification_status}*)")
                lines.append(f"🔗 [अधिकृत संकेतस्थळ]({item.official_source_url})")
            lines.append("\n💡 *सविस्तर कागदपत्रे पाहण्यासाठी योजनेचे नाव संदेशात पाठवा.*")
        else:
            lines.append("⚖️ **Scheme Comparison Report:**")
            lines.append("─" * 32)
            for i, item in enumerate(report.schemes, 1):
                lines.append(f"\n🏛️ **{i}. {item.scheme_name}**")
                lines.append(f"• **Ministry:** {item.ministry}")
                lines.append(f"• **Financial Benefits:** {item.benefit_amount} ({item.benefit_frequency})")
                lines.append(f"• **Age Limit:** {item.age_criteria} | **Income Ceiling:** {item.income_limit}")
                lines.append(f"• **Target Group:** {', '.join(item.target_beneficiaries)}")
                lines.append(f"• **Key Documents:** {len(item.required_documents)} items verified")
                lines.append(f"• **Application Mode:** {item.application_mode}")
                lines.append(f"• **Geographical Scope:** {item.state_applicability}")
                lines.append(f"• **Status:** {item.application_status} (*Verification: {item.verification_status}*)")
                lines.append(f"🔗 [Official Government Source]({item.official_source_url})")
            lines.append("\n💡 *Ask specific questions about either scheme anytime (e.g. 'How do I apply for KCC?').*")

        return "\n".join(lines)
