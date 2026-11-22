"""
Response Builder for Civicsaathi Chatbot.
Constructs respectful, simple, human, and localized citizen messages without bureaucratic jargon.
"""

from typing import Dict, Any, List
from database.models import CitizenProfile, SchemeRecord


class ResponseBuilder:
    @staticmethod
    def build_profile_summary(profile: CitizenProfile, language: str = "en") -> str:
        if language == "hi":
            return (
                "👤 **आपकी प्रोफाइल सारांश:**\n"
                f"- **राज्य:** {profile.state or 'दर्ज नहीं'}\n"
                f"- **आयु:** {f'{profile.age} वर्ष' if profile.age else 'दर्ज नहीं'}\n"
                f"- **व्यवसाय:** {profile.occupation or 'दर्ज नहीं'}\n"
                f"- **पारिवारिक आय:** {f'₹{profile.annual_family_income:,.0f}' if profile.annual_family_income else 'दर्ज नहीं'}\n"
                f"- **सामाजिक वर्ग:** {profile.category or 'दर्ज नहीं'}\n\n"
                "*(आप किसी भी समय 'reset' लिखकर अपनी जानकारी हटा सकते हैं)*"
            )
        elif language == "mr":
            return (
                "👤 **आपला प्रोफाइल सारांश:**\n"
                f"- **राज्य:** {profile.state or 'नोंदवलेले नाही'}\n"
                f"- **वय:** {f'{profile.age} वर्षे' if profile.age else 'नोंदवलेले नाही'}\n"
                f"- **व्यवसाय:** {profile.occupation or 'नोंदवलेले नाही'}\n"
                f"- **कौटुंबिक उत्पन्न:** {f'₹{profile.annual_family_income:,.0f}' if profile.annual_family_income else 'नोंदवलेले नाही'}\n"
                f"- **सामाजिक प्रवर्ग:** {profile.category or 'नोंदवलेले नाही'}\n\n"
                "*(आपण केव्हाही 'reset' लिहून आपली माहिती हटवू शकता)*"
            )
        else:
            return (
                "👤 **Your Citizen Profile Summary:**\n"
                f"- **State:** {profile.state or 'Not specified'}\n"
                f"- **Age:** {f'{profile.age} years' if profile.age else 'Not specified'}\n"
                f"- **Occupation:** {profile.occupation or 'Not specified'}\n"
                f"- **Annual Family Income:** {f'INR {profile.annual_family_income:,.0f}' if profile.annual_family_income else 'Not specified'}\n"
                f"- **Category:** {profile.category or 'Not specified'}\n\n"
                "*(Type 'reset' anytime to delete your profile data)*"
            )
