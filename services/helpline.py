"""
Government Helpline Service for Civicsaathi.
Provides verified national and state toll-free helpline numbers across India.
"""

from typing import List, Dict, Any


class HelplineService:
    VERIFIED_HELPLINES = [
        {
            "category": "Emergency & Safety",
            "name": "National Emergency Number",
            "number": "112",
            "scope": "Pan-India",
            "timing": "24x7",
            "description": "Unified emergency number for Police, Fire, and Ambulance services.",
        },
        {
            "category": "Agriculture & Farmers",
            "name": "Kisan Call Centre (KCC)",
            "number": "1800-180-1551",
            "scope": "Pan-India",
            "timing": "06:00 AM - 10:00 PM (All 7 days)",
            "description": "Direct consultation with agricultural scientists and scheme support in 22 regional languages.",
        },
        {
            "category": "Women & Child",
            "name": "Women in Distress Helpline",
            "number": "181 / 1091",
            "scope": "Pan-India",
            "timing": "24x7",
            "description": "Emergency response, counseling, and shelter assistance for women.",
        },
        {
            "category": "Women & Child",
            "name": "Childline (Pencil Portal / MoWCD)",
            "number": "1098",
            "scope": "Pan-India",
            "timing": "24x7",
            "description": "Emergency assistance and rescue for children in distress.",
        },
        {
            "category": "Healthcare",
            "name": "Ayushman Bharat PM-JAY",
            "number": "14555 / 1800-111-565",
            "scope": "Pan-India",
            "timing": "24x7",
            "description": "Hospital empanelment, card verification, and cashless claim queries.",
        },
        {
            "category": "Senior Citizens",
            "name": "Elderline (National Helpline for Senior Citizens)",
            "number": "14567",
            "scope": "Pan-India",
            "timing": "08:00 AM - 08:00 PM",
            "description": "Support, legal aid guidance, and rescue assistance for elderly citizens.",
        },
        {
            "category": "Consumer & Public Services",
            "name": "National Consumer Helpline",
            "number": "1915 / 1800-11-4000",
            "scope": "Pan-India",
            "timing": "09:30 AM - 05:30 PM",
            "description": "Consumer grievance redressal and unfair trade practice reporting.",
        },
        {
            "category": "Financial Inclusion",
            "name": "PMJDY / Jan Dhan Account Support",
            "number": "1800-180-1111 / 1800-11-0001",
            "scope": "Pan-India",
            "timing": "Normal Banking Hours",
            "description": "Basic banking, RuPay insurance claims, and Zero-balance account support.",
        },
        {
            "category": "Digital & Portal",
            "name": "myScheme Citizen Support",
            "number": "support-myscheme@gov.in",
            "scope": "Pan-India",
            "timing": "Email / Web",
            "description": "Official portal guidance for central and state scheme eligibility.",
        },
    ]

    @classmethod
    def get_helplines(cls, category: str = "All") -> List[Dict[str, Any]]:
        if category == "All":
            return cls.VERIFIED_HELPLINES
        return [h for h in cls.VERIFIED_HELPLINES if h["category"].lower() == category.lower()]
