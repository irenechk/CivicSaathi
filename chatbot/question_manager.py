"""
Conversational Question Manager for Civicsaathi.
Orchestrates a polite, non-intrusive step-by-step interview to build citizen profile.
Collects only necessary scheme evaluation attributes with citizen consent.
"""

from typing import List, Dict, Any, Optional
from database.models import CitizenProfile


class QuestionManager:
    QUESTIONS = {
        "state": {
            "en": "Which State or Union Territory do you currently reside in? (e.g. Maharashtra, Uttar Pradesh, Delhi)",
            "hi": "आप वर्तमान में किस राज्य या केंद्र शासित प्रदेश में रहते हैं? (जैसे महाराष्ट्र, उत्तर प्रदेश, दिल्ली)",
            "mr": "आपण सध्या कोणत्या राज्यात किंवा केंद्रशासित प्रदेशात राहता? (उदा. महाराष्ट्र, उत्तर प्रदेश, दिल्ली)",
        },
        "age": {
            "en": "May I know your age in years?",
            "hi": "क्या आप अपनी आयु (उम्र) बता सकते हैं?",
            "mr": "कृपया आपले वय किती वर्षे आहे ते सांगू शकाल का?",
        },
        "occupation": {
            "en": "What is your primary occupation or profession? (e.g., Farmer, Student, Artisan, Self-employed, Unorganized worker, Homemaker)",
            "hi": "आपका मुख्य व्यवसाय या कार्य क्या है? (जैसे किसान, छात्र, कारीगर, स्वरोजगार, असंगठित श्रमिक, गृहिणी)",
            "mr": "आपला मुख्य व्यवसाय किंवा काम काय आहे? (उदा. शेतकरी, विद्यार्थी, कारागीर, स्वयंरोजगार, असंघटित कामगार, गृहिणी)",
        },
        "annual_family_income": {
            "en": "Approximately what is your annual family income? (e.g., INR 1.5 Lakh, INR 3 Lakh)",
            "hi": "आपकी वार्षिक पारिवारिक आय लगभग कितनी है? (जैसे 1.5 लाख, 3 लाख रुपये)",
            "mr": "आपले अंदाजे वार्षिक कौटुंबिक उत्पन्न किती आहे? (उदा. १.५ लाख, ३ लाख रुपये)",
        },
        "category": {
            "en": "Which social category do you belong to? (General, OBC, SC, ST, or Minority)",
            "hi": "आप किस सामाजिक वर्ग से संबंधित हैं? (सामान्य / General, ओबीसी / OBC, एससी / SC, एसटी / ST, अल्पसंख्यक / Minority)",
            "mr": "आपण कोणत्या प्रवर्गाशी संबंधित आहात? (खुला / General, ओबीसी / OBC, एससी / SC, एसटी / ST, अल्पसंख्याक / Minority)",
        },
    }

    @staticmethod
    def get_next_question(profile: CitizenProfile, language: str = "en") -> Optional[Dict[str, str]]:
        """Identifies the next essential missing attribute and generates a localized question."""
        order = ["state", "age", "occupation", "annual_family_income", "category"]
        for field in order:
            val = getattr(profile, field, None)
            if val is None:
                q_text = QuestionManager.QUESTIONS[field].get(language, QuestionManager.QUESTIONS[field]["en"])
                return {"field": field, "question": q_text}
        return None
