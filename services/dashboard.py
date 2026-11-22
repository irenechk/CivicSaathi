"""
Citizen Dashboard Service for Civicsaathi.
Aggregates profile, saved schemes, recommendations, eligibility outcomes,
missing documents, view history, and privacy/data management controls.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path

from database.models import CitizenProfile, CitizenDashboardData
from database.repository import (
    CitizenProfileRepository,
    CitizenSavedSchemeRepository,
    CitizenDocumentRepository,
    SchemeRepository,
)
from services.recommendation import RecommendationService
from services.readiness import ApplicationReadinessTracker


class CitizenDashboardService:
    def __init__(
        self,
        profile_repo: Optional[CitizenProfileRepository] = None,
        saved_repo: Optional[CitizenSavedSchemeRepository] = None,
        doc_repo: Optional[CitizenDocumentRepository] = None,
        scheme_repo: Optional[SchemeRepository] = None,
        db_path: Optional[Path] = None,
    ):
        self.profile_repo = profile_repo or CitizenProfileRepository(db_path=db_path)
        self.saved_repo = saved_repo or CitizenSavedSchemeRepository(db_path=db_path)
        self.doc_repo = doc_repo or CitizenDocumentRepository(db_path=db_path)
        self.scheme_repo = scheme_repo or SchemeRepository(db_path=db_path)
        self.recommender = RecommendationService(repository=self.scheme_repo)
        self.readiness_tracker = ApplicationReadinessTracker(scheme_repo=self.scheme_repo, doc_repo=self.doc_repo)

    def get_dashboard_data(self, user_id: str, language: str = "en") -> CitizenDashboardData:
        """Assembles complete citizen dashboard object."""
        profile = self.profile_repo.get_profile(user_id) or CitizenProfile(user_id=user_id, language=language)

        # Saved schemes
        saved_ids = self.saved_repo.get_saved_schemes(user_id)
        saved_schemes = []
        for sid in saved_ids:
            s = self.scheme_repo.get_scheme_by_id(sid)
            if s:
                saved_schemes.append({
                    "scheme_id": s.scheme_id,
                    "scheme_name": f"{s.scheme_name} ({', '.join(s.alternate_names)})" if s.alternate_names else s.scheme_name,
                    "ministry": s.ministry,
                    "benefit": s.benefit_amount,
                })

        # Recommendations & Eligibility
        ranked_reports = self.recommender.get_recommendations_for_profile(profile)[:5]
        rec_list = []
        elig_summaries = []
        all_missing_docs = set()

        for rep in ranked_reports:
            s = self.scheme_repo.get_scheme_by_id(rep.scheme_id)
            rec_list.append({
                "scheme_id": rep.scheme_id,
                "scheme_name": f"{s.scheme_name} ({', '.join(s.alternate_names)})" if s and s.alternate_names else rep.scheme_name,
                "status": rep.overall_status,
                "benefit": s.benefit_amount if s else None,
            })
            elig_summaries.append({
                "scheme_name": rep.scheme_name,
                "status": rep.overall_status,
                "missing_fields": rep.missing_fields,
            })
            if s:
                readiness = self.readiness_tracker.evaluate_readiness(s, user_id=user_id, language=language)
                all_missing_docs.update(readiness.missing_mandatory)

        # View history
        recent_views = self.saved_repo.get_view_history(user_id, limit=4)

        return CitizenDashboardData(
            profile=profile,
            saved_schemes=saved_schemes,
            recommended_schemes=rec_list,
            eligibility_summaries=elig_summaries,
            missing_documents=sorted(list(all_missing_docs)),
            recently_viewed=recent_views,
            consent_given=True,
        )

    def format_dashboard_telegram(self, data: CitizenDashboardData, language: str = "en") -> str:
        """Renders rich executive citizen dashboard for Telegram."""
        p = data.profile
        name = p.full_name or ("नागरिक" if language != "en" else "Citizen")
        state = p.state or "Pan-India"
        occ = p.occupation or "General"
        inc = f"₹{p.annual_family_income:,.0f}" if p.annual_family_income else "Not specified"
        lang_label = {"en": "English 🇬🇧", "hi": "हिंदी 🇮🇳", "mr": "मराठी 🇮🇳"}.get(p.language or language, "English")

        lines = []
        if language == "hi":
            lines.append(f"👤 **नागरिक प्रोफाइल डैशबोर्ड (Citizen Dashboard)**")
            lines.append("─" * 32)
            lines.append(f"👋 **नमस्ते, {name} जी!**")
            lines.append(f"• **राज्य:** {state} | **आयु:** {p.age or 'अज्ञात'} वर्ष | **लिंग:** {p.gender or 'N/A'}")
            lines.append(f"• **व्यवसाय:** {occ} | **वार्षिक आय:** {inc}")
            lines.append(f"• **सामाजिक वर्ग:** {p.category or 'सामान्य'} | **भाषा:** {lang_label}")

            lines.append(f"\n🎯 **पात्र सरकारी योजनाएं ({len(data.recommended_schemes)}):**")
            if data.recommended_schemes:
                for s in data.recommended_schemes[:4]:
                    status_icon = "🟢" if s["status"] == "ELIGIBLE" else "🟡"
                    lines.append(f"• {status_icon} **{s['scheme_name']}**: {s['benefit'] or 'कल्याणकारी लाभ'}")
            else:
                lines.append("• *अभी कोई सिफारिश नहीं मिली। 'पुनः जांचें' पर टैप करें।*")

            lines.append(f"\n📑 **सहेजी गई योजनाएं ({len(data.saved_schemes)}):**")
            if data.saved_schemes:
                for s in data.saved_schemes:
                    lines.append(f"• 📌 **{s['scheme_name']}**")
            else:
                lines.append("• *आपने अभी कोई योजना बुकमार्क नहीं की है।*")

            if data.missing_documents:
                lines.append(f"\n⚠️ **आवश्यक दस्तावेज़ जो तैयार करने हैं ({len(data.missing_documents)}):**")
                for d in data.missing_documents[:4]:
                    lines.append(f"• ✗ {d}")

            if data.recently_viewed:
                lines.append("\n🕒 **हाल ही में देखी गई योजनाएं:**")
                for v in data.recently_viewed[:3]:
                    lines.append(f"• 👁️ {v['scheme_name']}")

            lines.append("\n⚙️ **डेटा नियंत्रण एवं गोपनीयता:**")
            lines.append("• अपनी प्रोफाइल बदलने के लिए `/start` दबाएं।")
            lines.append("• सभी रिकॉर्ड हमेशा के लिए मिटाने हेतु `/reset` दबाएं।")
        elif language == "mr":
            lines.append(f"👤 **नागरिक प्रोफाईल डॅशबोर्ड (Citizen Dashboard)**")
            lines.append("─" * 32)
            lines.append(f"👋 **नमस्कार, {name}!**")
            lines.append(f"• **राज्य:** {state} | **वय:** {p.age or 'अज्ञात'} वर्षे | **लिंग:** {p.gender or 'N/A'}")
            lines.append(f"• **व्यवसाय:** {occ} | **कौटुंबिक उत्पन्न:** {inc}")
            lines.append(f"• **प्रवर्ग:** {p.category or 'सर्वसाधारण'} | **भाषा:** {lang_label}")

            lines.append(f"\n🎯 **पात्र सरकारी योजना ({len(data.recommended_schemes)}):**")
            if data.recommended_schemes:
                for s in data.recommended_schemes[:4]:
                    status_icon = "🟢" if s["status"] == "ELIGIBLE" else "🟡"
                    lines.append(f"• {status_icon} **{s['scheme_name']}**: {s['benefit'] or 'शासकीय लाभ'}")
            else:
                lines.append("• *सध्या कोणतीही शिफारस नाही.*")

            lines.append(f"\n📑 **जतन केलेल्या योजना ({len(data.saved_schemes)}):**")
            if data.saved_schemes:
                for s in data.saved_schemes:
                    lines.append(f"• 📌 **{s['scheme_name']}**")
            else:
                lines.append("• *अद्याप कोणतीही योजना जतन केलेली नाही.*")

            if data.missing_documents:
                lines.append(f"\n⚠️ **तयार करावयाची कागदपत्रे ({len(data.missing_documents)}):**")
                for d in data.missing_documents[:4]:
                    lines.append(f"• ✗ {d}")

            lines.append("\n⚙️ **डेटा गोपनीयता व नियंत्रण:**")
            lines.append("• प्रोफाईल अपडेट करण्यासाठी `/start` वापरा.")
            lines.append("• संपूर्ण डेटा हटवण्यासाठी `/reset` वापरा.")
        else:
            lines.append(f"👤 **Citizen Profile Dashboard**")
            lines.append("─" * 32)
            lines.append(f"👋 **Welcome, {name}!**")
            lines.append(f"• **State:** {state} | **Age:** {p.age or 'N/A'} yrs | **Gender:** {p.gender or 'N/A'}")
            lines.append(f"• **Occupation:** {occ} | **Family Income:** {inc}")
            lines.append(f"• **Category:** {p.category or 'General'} | **Language:** {lang_label}")

            lines.append(f"\n🎯 **Recommended Government Schemes ({len(data.recommended_schemes)}):**")
            if data.recommended_schemes:
                for s in data.recommended_schemes[:4]:
                    status_icon = "🟢" if s["status"] == "ELIGIBLE" else "🟡"
                    lines.append(f"• {status_icon} **{s['scheme_name']}**: {s['benefit'] or 'Welfare assistance'}")
            else:
                lines.append("• *No recommendations yet. Run an assessment via /start.*")

            lines.append(f"\n📑 **Saved Schemes / Bookmarks ({len(data.saved_schemes)}):**")
            if data.saved_schemes:
                for s in data.saved_schemes:
                    lines.append(f"• 📌 **{s['scheme_name']}**")
            else:
                lines.append("• *No schemes bookmarked yet.*")

            if data.missing_documents:
                lines.append(f"\n⚠️ **Key Missing Documents Across Eligible Schemes ({len(data.missing_documents)}):**")
                for d in data.missing_documents[:4]:
                    lines.append(f"• ✗ {d}")

            if data.recently_viewed:
                lines.append("\n🕒 **Recently Viewed Schemes:**")
                for v in data.recently_viewed[:3]:
                    lines.append(f"• 👁️ {v['scheme_name']}")

            lines.append("\n⚙️ **Privacy & Data Sovereignty:**")
            lines.append("• To update your profile: Type `/start`")
            lines.append("• To permanently delete all personal data (DPDP Act): Type `/reset`")

        return "\n".join(lines)
