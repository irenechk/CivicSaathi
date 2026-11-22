"""
Citizen Profile Extractor for Civicsaathi Chatbot.
Parses natural conversational statements into structured profile attributes.
Strict Privacy Rule:
- NEVER extracts or asks for Aadhaar, OTPs, bank passwords, or biometric data.
- Leaves unmentioned fields as None.
"""

import re
from typing import Dict, Any, Optional
from database.models import CitizenProfile

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh"
]

OCCUPATIONS = [
    "farmer", "cultivator", "artisan", "craftsperson", "street_vendor", "student",
    "unorganized_worker", "construction_worker", "employed", "self_employed", "homemaker"
]


class ProfileExtractor:
    @staticmethod
    def extract_from_text(text: str, current_profile: Optional[CitizenProfile] = None) -> CitizenProfile:
        profile = current_profile.model_copy() if current_profile else CitizenProfile()
        text_lower = text.lower()

        # 1. Extract Age
        age_match = re.search(r"\b(?:i am|age is|age|i'm)?\s*([1-9][0-9]?)\s*(?:years?|yrs?|yr)?\s*(?:old)?\b", text_lower)
        if age_match:
            try:
                age_val = int(age_match.group(1))
                if 1 <= age_val <= 110:
                    profile.age = age_val
            except ValueError:
                pass

        # 2. Extract State
        for st in INDIAN_STATES:
            if st.lower() in text_lower:
                profile.state = st
                break

        # 3. Extract Gender
        if any(w in text_lower for w in ["female", "woman", "girl", "lady", "महिला", "स्त्री"]):
            profile.gender = "female"
        elif any(w in text_lower for w in ["male", "man", "boy", "gentleman", "पुरुष"]):
            profile.gender = "male"

        # 4. Extract Income
        income_match = re.search(r"(?:income|salary|earn|earning|कमाई|उत्पन्न)\s*(?:is|of|about)?\s*(?:inr|rs|₹)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(lakh|lac|k|crore)?", text_lower)
        if income_match:
            try:
                num_str = income_match.group(1).replace(",", "")
                val = float(num_str)
                multiplier = income_match.group(2)
                if multiplier in ("lakh", "lac"):
                    val *= 100000
                elif multiplier == "k":
                    val *= 1000
                elif multiplier == "crore":
                    val *= 10000000
                profile.annual_family_income = val
            except ValueError:
                pass

        # 5. Extract Occupation
        for occ in OCCUPATIONS:
            clean_occ = occ.replace("_", " ")
            if clean_occ in text_lower:
                profile.occupation = occ
                break
        if "farmer" in text_lower or "किसान" in text_lower or "शेतकरी" in text_lower:
            profile.occupation = "farmer"
            profile.owns_cultivable_land = True
        elif "student" in text_lower or "छात्र" in text_lower or "विद्यार्थी" in text_lower:
            profile.occupation = "student"
        elif "vendor" in text_lower or "फेरीवाला" in text_lower or "विक्रेता" in text_lower:
            profile.occupation = "street_vendor"
        elif "artisan" in text_lower or "कारीगर" in text_lower or "शिल्पकार" in text_lower:
            profile.occupation = "artisan"

        # 6. Extract Social Category
        if "sc" in text_lower.split() or "scheduled caste" in text_lower:
            profile.category = "SC"
        elif "st" in text_lower.split() or "scheduled tribe" in text_lower:
            profile.category = "ST"
        elif "obc" in text_lower.split() or "other backward" in text_lower:
            profile.category = "OBC"
        elif "ebc" in text_lower.split():
            profile.category = "EBC"
        elif "general" in text_lower.split() or "open" in text_lower:
            profile.category = "General"

        # 7. Extract BPL / Landownership
        if "bpl" in text_lower or "ration card" in text_lower:
            profile.has_bpl_card = True

        return profile
