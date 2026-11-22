"""
Central Internationalization (i18n) Module for Civicsaathi.
Supports English (en), Hindi (hi), and Marathi (mr).
All text adheres to a friendly, respectful, simple, and human conversational tone.
"""

from typing import Dict, Any

# Supported languages metadata
SUPPORTED_LANGUAGES: Dict[str, Dict[str, str]] = {
    "en": {"code": "en", "name": "English", "label": "English 🇬🇧"},
    "hi": {"code": "hi", "name": "Hindi", "label": "हिंदी 🇮🇳"},
    "mr": {"code": "mr", "name": "Marathi", "label": "मराठी 🇮🇳"},
}

DEFAULT_LANGUAGE = "en"

# First-time welcome & language prompt
INITIAL_LANGUAGE_PROMPT = (
    "Namaste! Welcome to Civicsaathi 🇮🇳\n\n"
    "Before we begin, please choose your preferred language."
)

LANGUAGE_CHANGE_PROMPT = (
    "🌐 *Choose your preferred language / अपनी पसंदीदा भाषा चुनें / आपली पसंतीची भाषा निवडा:*"
)

# Central Translation Catalog
STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "welcome_back": (
            "Namaste! Welcome to Civicsaathi 🇮🇳\n\n"
            "Your friendly government scheme assistance companion.\n\n"
            "I can help you discover schemes, understand eligibility, prepare documents and find official government assistance.\n\n"
            "Let's make government benefits easier to access!"
        ),
        "lang_confirmed": "✅ Language set to *English 🇬🇧*.\nWelcome to Civicsaathi!",
        # Main Menu Buttons
        "btn_schemes": "🔍 Find Government Schemes",
        "btn_profile": "👤 My Profile",
        "btn_recommended": "⭐ My Recommended Schemes",
        "btn_documents": "📄 Required Documents",
        "btn_helpline": "📞 Government Helpline",
        "btn_language": "🌐 Change Language",
        "btn_help": "ℹ️ Help",
        # Button responses (Coming Soon & Live Info)
        "schemes_response": (
            "🔍 *Find Government Schemes*\n\n"
            "This feature is coming soon in the next development phase!\n\n"
            "You will be able to search and explore central and state government schemes easily."
        ),
        "profile_response": (
            "👤 *My Profile*\n\n"
            "Citizen profile management is coming soon in the next development phase!\n\n"
            "Setting up your profile (age, occupation, state, category) will allow Civicsaathi to recommend schemes tailored specifically for you."
        ),
        "recommended_response": (
            "⭐ *My Recommended Schemes*\n\n"
            "AI-powered scheme recommendations based on your profile will be available in the upcoming phase!\n\n"
            "We are working on intelligent matching to ensure you never miss any benefit."
        ),
        "documents_response": (
            "📄 *Required Documents Guide*\n\n"
            "Document checklists and eligibility verification are coming soon in the next phase!\n\n"
            "You will receive step-by-step guidance on certificates (Aadhaar, income certificate, caste certificate, ration card, etc.)."
        ),
        "helpline_response": (
            "📞 *Important Government Helplines 🇮🇳*\n\n"
            "Here are verified national helpline numbers available to assist citizens:\n\n"
            "• 🚨 *National Emergency:* 112\n"
            "• 🌾 *Kisan Call Centre (Farmers):* 1800-180-1551\n"
            "• 👩 *Women Helpline:* 181 / 1091\n"
            "• 🛒 *National Consumer Helpline:* 1915 / 1800-11-4000\n"
            "• 🏥 *Ayushman Bharat (Health Services):* 14555\n"
            "• 👶 *Childline:* 1098\n"
            "• 👴 *Elderline (Senior Citizens):* 14567\n"
            "• 🌐 *National Portal of India:* india.gov.in\n\n"
            "All helpline numbers are toll-free and accessible across India."
        ),
        "help_text": (
            "🏛️ *Civicsaathi Help & Guidance* 🇮🇳\n\n"
            "Civicsaathi is your AI companion designed to make government welfare schemes simple, transparent, and accessible.\n\n"
            "📋 *Available Commands:*\n"
            "• /start — Open the main menu & welcome screen\n"
            "• /language — Change your preferred language\n"
            "• /help — Show this help information\n\n"
            "🚀 *Current Status: Phase 2 (Multilingual Experience)*\n"
            "Currently supported in English, Hindi, and Marathi.\n\n"
            "Need assistance? Just tap any menu button below or send a message!"
        ),
        "unknown_text": (
            "❓ *Command or message not recognized*\n\n"
            "I'm here to help you with government schemes.\n\n"
            "• Type /start to open the main menu\n"
            "• Type /language to switch language\n"
            "• Type /help for assistance"
        ),
        "main_menu_prompt": "Please choose an option below:",
    },
    "hi": {
        "welcome_back": (
            "नमस्ते! नागरिक साथी (Civicsaathi) में आपका स्वागत है 🇮🇳\n\n"
            "सरकारी योजनाओं की जानकारी के लिए आपका अपना डिजिटल साथी।\n\n"
            "मैं आपको नई योजनाएँ खोजने, पात्रता समझने, ज़रूरी दस्तावेज़ तैयार करने और सरकारी सहायता प्राप्त करने में मदद कर सकता हूँ।\n\n"
            "आइए, सरकारी योजनाओं का लाभ पाना और आसान बनाएँ!"
        ),
        "lang_confirmed": "✅ भाषा सेट की गई: *हिंदी 🇮🇳*।\nनागरिक साथी में आपका स्वागत है!",
        # Main Menu Buttons
        "btn_schemes": "🔍 सरकारी योजनाएँ खोजें",
        "btn_profile": "👤 मेरी प्रोफाइल",
        "btn_recommended": "⭐ अनुशंसित योजनाएँ",
        "btn_documents": "📄 आवश्यक दस्तावेज़",
        "btn_helpline": "📞 सरकारी हेल्पलाइन",
        "btn_language": "🌐 भाषा बदलें",
        "btn_help": "ℹ️ सहायता (Help)",
        # Button responses (Coming Soon & Live Info)
        "schemes_response": (
            "🔍 *सरकारी योजनाएँ खोजें*\n\n"
            "यह सुविधा अगले चरण में जल्द आ रही है!\n\n"
            "आप केंद्र एवं राज्य सरकार की सभी कल्याणकारी योजनाओं को आसानी से खोज सकेंगे।"
        ),
        "profile_response": (
            "👤 *मेरी प्रोफाइल*\n\n"
            "नागरिक प्रोफाइल सुविधा अगले चरण में जल्द आ रही है!\n\n"
            "अपनी जानकारी (आयु, व्यवसाय, राज्य, श्रेणी) जोड़कर आप अपने लिए विशेष रूप से उपयुक्त योजनाएँ प्राप्त कर सकेंगे।"
        ),
        "recommended_response": (
            "⭐ *मेरे लिए अनुशंसित योजनाएँ*\n\n"
            "आपकी प्रोफाइल के आधार पर AI द्वारा चुनी गई सर्वोत्तम सरकारी योजनाओं की सुविधा अगले चरण में उपलब्ध होगी!\n\n"
            "हम इस पर काम कर रहे हैं ताकि कोई भी योजना आपसे छूटे नहीं।"
        ),
        "documents_response": (
            "📄 *आवश्यक दस्तावेज़ मार्गदर्शिका*\n\n"
            "दस्तावेज़ों की सूची और पात्रता की जाँच की सुविधा अगले चरण में जल्द आ रही है!\n\n"
            "आपको आधार कार्ड, आय प्रमाण पत्र, जाति प्रमाण पत्र, राशन कार्ड आदि से जुड़ी पूरी जानकारी मिलेगी।"
        ),
        "helpline_response": (
            "📞 *महत्वपूर्ण सरकारी हेल्पलाइन 🇮🇳*\n\n"
            "नागरिकों की सहायता के लिए उपयोगी आधिकारिक राष्ट्रीय हेल्पलाइन नंबर:\n\n"
            "• 🚨 *राष्ट्रीय आपातकालीन सेवा:* 112\n"
            "• 🌾 *किसान कॉल सेंटर (कृषि सहायता):* 1800-180-1551\n"
            "• 👩 *महिला हेल्पलाइन:* 181 / 1091\n"
            "• 🛒 *राष्ट्रीय उपभोक्ता हेल्पलाइन:* 1915 / 1800-11-4000\n"
            "• 🏥 *आयुष्मान भारत (स्वास्थ्य योजना):* 14555\n"
            "• 👶 *चाइल्डलाइन (बच्चों की सहायता):* 1098\n"
            "• 👴 *एल्डरलाइन (वरिष्ठ नागरिक):* 14567\n"
            "• 🌐 *राष्ट्रीय सरकारी पोर्टल:* india.gov.in\n\n"
            "ये सभी नंबर टोल-फ्री (निःशुल्क) हैं और पूरे भारत में उपलब्ध हैं।"
        ),
        "help_text": (
            "🏛️ *नागरिक साथी सहायता व मार्गदर्शन* 🇮🇳\n\n"
            "नागरिक साथी एक सरल और भरोसेमंद माध्यम है जिससे आप सरकारी योजनाओं की जानकारी आसानी से पा सकते हैं।\n\n"
            "📋 *उपलब्ध कमांड:*\n"
            "• /start — मुख्य मेनू और स्वागत संदेश\n"
            "• /language — भाषा बदलने के लिए\n"
            "• /help — सहायता और जानकारी देखने के लिए\n\n"
            "🚀 *वर्तमान स्थिति: चरण 2 (बहुभाषी अनुभव)*\n"
            "वर्तमान में हिंदी, अंग्रेज़ी और मराठी भाषा उपलब्ध है।\n\n"
            "किसी भी सहायता के लिए नीचे दिए गए बटन पर टैप करें।"
        ),
        "unknown_text": (
            "❓ *संदेश या कमांड समझ नहीं आया*\n\n"
            "मैं सरकारी योजनाओं में आपकी मदद के लिए यहाँ हूँ।\n\n"
            "• मुख्य मेनू के लिए /start भेजें\n"
            "• भाषा बदलने के लिए /language भेजें\n"
            "• सहायता के लिए /help भेजें"
        ),
        "main_menu_prompt": "कृपया नीचे दिए गए विकल्पों में से चुनें:",
    },
    "mr": {
        "welcome_back": (
            "नमस्कार! नागरीक साथी (Civicsaathi) मध्ये आपले सहर्ष स्वागत आहे 🇮🇳\n\n"
            "शासकीय योजनांच्या माहितीसाठी आपला हक्काचा डिजिटल मित्र.\n\n"
            "मी आपल्याला विविध योजना शोधण्यात, पात्रता समजून घेण्यात, कागदपत्रे तयार करण्यात आणि शासकीय मदत मिळवण्यात सहकार्य करेन.\n\n"
            "चला, सरकारी योजनांचा लाभ मिळवणे अधिक सोपे करूया!"
        ),
        "lang_confirmed": "✅ भाषा निवडली: *मराठी 🇮🇳*.\nनागरीक साथी मध्ये आपले स्वागत आहे!",
        # Main Menu Buttons
        "btn_schemes": "🔍 शासकीय योजना शोधा",
        "btn_profile": "👤 माझे प्रोफाइल",
        "btn_recommended": "⭐ शिफारस केलेल्या योजना",
        "btn_documents": "📄 आवश्यक कागदपत्रे",
        "btn_helpline": "📞 शासकीय हेल्पलाइन",
        "btn_language": "🌐 भाषा बदला",
        "btn_help": "ℹ️ मदत (Help)",
        # Button responses (Coming Soon & Live Info)
        "schemes_response": (
            "🔍 *शासकीय योजना शोधा*\n\n"
            "ही सुविधा पुढील टप्प्यात लवकरच येत आहे!\n\n"
            "आपण केंद्र आणि राज्य शासनाच्या सर्व कल्याणकारी योजना सहजपणे शोधू शकाल."
        ),
        "profile_response": (
            "👤 *माझे प्रोफाइल*\n\n"
            "नागरीक प्रोफाइल सुविधा पुढील टप्प्यात लवकरच येत आहे!\n\n"
            "आपली माहिती (वय, व्यवसाय, राज्य, प्रवर्ग) भरून आपल्याला योग्य अशा योजनांची अचूक माहिती मिळेल."
        ),
        "recommended_response": (
            "⭐ *माझ्यासाठी शिफारस केलेल्या योजना*\n\n"
            "आपल्या प्रोफाइलवर आधारित AI द्वारे योजना शिफारस करण्याची सुविधा पुढील टप्प्यात उपलब्ध होईल!\n\n"
            "कोणतीही शासकीय योजना आपल्यापासून सुटू नये यासाठी आम्ही प्रयत्नशील आहोत."
        ),
        "documents_response": (
            "📄 *आवश्यक कागदपत्रे मार्गदर्शिका*\n\n"
            "कागदपत्रांची यादी आणि पात्रता पडताळणी पुढील टप्प्यात उपलब्ध होणार आहे!\n\n"
            "आपल्याला आधार कार्ड, उत्पन्न दाखला, जात प्रमाणपत्र, रेशन कार्ड इत्यादी बाबत संपूर्ण मार्गदर्शन मिळेल."
        ),
        "helpline_response": (
            "📞 *महत्त्वाच्या शासकीय हेल्पलाइन 🇮🇳*\n\n"
            "नागरिकांच्या मदतीसाठी अधिकृत राष्ट्रीय हेल्पलाइन क्रमांक:\n\n"
            "• 🚨 *राष्ट्रीय आपत्कालीन सेवा:* 112\n"
            "• 🌾 *किसान कॉल सेंटर (शेतकरी मदत):* 1800-180-1551\n"
            "• 👩 *महिला हेल्पलाइन:* 181 / 1091\n"
            "• 🛒 *राष्ट्रीय ग्राहक हेल्पलाइन:* 1915 / 1800-11-4000\n"
            "• 🏥 *आयुष्मान भारत (आरोग्य सेवा):* 14555\n"
            "• 👶 *चाइल्डलाइन (बाल मदत):* 1098\n"
            "• 👴 *एल्डरलाइन (ज्येष्ठ नागरिक):* 14567\n"
            "• 🌐 *अधिकृत शासकीय पोर्टल:* india.gov.in\n\n"
            "हे सर्व क्रमांक टोल-फ्री (मोफत) असून संपूर्ण भारतात उपलब्ध आहेत."
        ),
        "help_text": (
            "🏛️ *नागरीक साथी मदत आणि मार्गदर्शन* 🇮🇳\n\n"
            "शासकीय कल्याणकारी योजना सोप्या आणि सुलभ रीतीने समजून घेण्यासाठी नागरीक साथी आपला मार्गदर्शक आहे.\n\n"
            "📋 *उपलब्ध कमांड:*\n"
            "• /start — मुख्य मेनू आणि स्वागत संदेश\n"
            "• /language — भाषा बदलण्यासाठी\n"
            "• /help — मदत आणि माहिती पाहण्यासाठी\n\n"
            "🚀 *सध्याची स्थिती: टप्पा २ (बहुभाषिक अनुभव)*\n"
            "सध्या इंग्रजी, हिंदी आणि मराठी भाषांमध्ये उपलब्ध आहे.\n\n"
            "कोणत्याही मदतीसाठी खालील बटणावर टॅप करा."
        ),
        "unknown_text": (
            "❓ *संदेश किंवा कमांड समजली नाही*\n\n"
            "मी शासकीय योजनांच्या संदर्भात आपल्याला मदत करण्यासाठी येथे आहे.\n\n"
            "• मुख्य मेनूसाठी /start पाठवा\n"
            "• भाषा बदलण्यासाठी /language पाठवा\n"
            "• मदतीसाठी /help पाठवा"
        ),
        "main_menu_prompt": "कृपया खालील पर्यायांपैकी एक निवडा:",
    },
}


def get_text(key: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """
    Retrieve translated string for a given key and language.
    Falls back to English if key or language is missing.
    """
    lang_dict = STRINGS.get(lang, STRINGS[DEFAULT_LANGUAGE])
    if key in lang_dict:
        return lang_dict[key]
    return STRINGS[DEFAULT_LANGUAGE].get(key, f"[{key}]")


def is_valid_language(lang_code: str) -> bool:
    """Check if the provided language code is supported."""
    return lang_code in SUPPORTED_LANGUAGES
