"""
Privacy Guard and Sensitive Credential Protection for Civicsaathi.
Complies with Digital Personal Data Protection (DPDP) Act, 2023.
Ensures zero collection of Aadhaar numbers, OTPs, passwords, or banking credentials.
"""

import re
from typing import Dict, Any, Optional


class PrivacyGuard:
    # 12-digit Aadhaar pattern (with or without spaces/hyphens)
    AADHAAR_REGEX = re.compile(r"\b[2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4}\b")

    # OTP pattern (4 to 8 digits with context keywords)
    OTP_REGEX = re.compile(r"\b(?:otp|one[- ]time[- ]password|verification code)\s*(?:is|:|-|=)?\s*(\d{4,8})\b", re.IGNORECASE)

    # Password / PIN pattern
    PASSWORD_REGEX = re.compile(r"\b(?:password|passcode|mpin|atm pin|cvv)\s*(?:is|:|-|=)?\s*(\S+)\b", re.IGNORECASE)

    # Bank account numbers preceded by bank keywords
    BANK_REGEX = re.compile(r"\b(?:account|ac|a/c|bank|card)\s*(?:no|num|number)?\s*(?:is|:|-|=)?\s*(\d{9,18})\b", re.IGNORECASE)

    @classmethod
    def check_sensitive_content(cls, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Inspects citizen input for private credentials and masks them.
        Returns safety report with localized warning if sensitive data is detected.
        """
        detected_types = []
        sanitized = text

        # Check Aadhaar
        if cls.AADHAAR_REGEX.search(text):
            detected_types.append("Aadhaar Number")
            sanitized = cls.AADHAAR_REGEX.sub("[REDACTED_AADHAAR]", sanitized)

        # Check OTP
        if cls.OTP_REGEX.search(text):
            detected_types.append("OTP / Security Code")
            sanitized = cls.OTP_REGEX.sub(r"otp: [REDACTED_OTP]", sanitized)

        # Check Password / PIN
        if cls.PASSWORD_REGEX.search(text):
            detected_types.append("Password / PIN")
            sanitized = cls.PASSWORD_REGEX.sub(r"password: [REDACTED_PIN]", sanitized)

        # Check Bank Account
        if cls.BANK_REGEX.search(text):
            detected_types.append("Bank Account / Card Details")
            sanitized = cls.BANK_REGEX.sub(r"account: [REDACTED_ACCOUNT]", sanitized)

        has_sensitive = len(detected_types) > 0
        warning = ""
        if has_sensitive:
            if language == "hi":
                warning = (
                    "🔒 **सुरक्षा चेतावनी:** आपकी सुरक्षा के लिए आधार संख्या, पासवर्ड, ओटीपी अथवा बैंक खाता विवरण साझा न करें। "
                    "सिविकसाथी (Civicsaathi) कभी भी निजी क्रेडेंशियल्स नहीं मांगता। हमने यह जानकारी सुरक्षित रूप से हटा दी है।"
                )
            elif language == "mr":
                warning = (
                    "🔒 **सुरक्षा सूचना:** आपल्या सुरक्षिततेसाठी कृपया आधार क्रमांक, ओटीपी, पासवर्ड किंवा बँक खाते तपशील पाठवू नका. "
                    "सिविकसाथी (Civicsaathi) कधीही खाजगी क्रेडेंशियल्स मागत नाही. आम्ही ही माहिती सुरक्षितपणे काढून टाकली आहे."
                )
            else:
                warning = (
                    "🔒 **Security Advisory:** For your privacy and security under the DPDP Act, never share Aadhaar numbers, "
                    "OTPs, passwords, or bank account numbers. Civicsaathi will never ask for confidential credentials. "
                    "This sensitive data was automatically redacted."
                )

        return {
            "has_sensitive_data": has_sensitive,
            "detected_types": detected_types,
            "sanitized_text": sanitized,
            "warning": warning,
        }

    @classmethod
    def get_consent_dialog(cls, language: str = "en") -> str:
        """Returns DPDP Act compliance consent text."""
        if language == "hi":
            return (
                "🛡️ **गोपनीयता एवं सहमति (Privacy & Consent):**\n\n"
                "डिजिटल व्यक्तिगत डेटा संरक्षण (DPDP) अधिनियम के तहत, आपकी दर्ज जानकारी (आयु, राज्य, व्यवसाय) "
                "केवल उपयुक्त सरकारी योजनाओं की पहचान के लिए उपयोग की जाएगी।\n\n"
                "• हम कोई भी आधार नंबर, बैंक विवरण अथवा पासवर्ड एकत्र नहीं करते।\n"
                "• आप कभी भी अपना डेटा पूरी तरह डिलीट ('/reset') कर सकते हैं।\n\n"
                "क्या आप अपनी प्रोफाइल सुरक्षित रखने हेतु सहमति देते हैं?"
            )
        elif language == "mr":
            return (
                "🛡️ **गोपनीयता आणि संमती (Privacy & Consent):**\n\n"
                "डिजिटल वैयक्तिक डेटा संरक्षण (DPDP) कायद्यानुसार, आपली माहिती (वय, राज्य, व्यवसाय) "
                "केवळ पात्र सरकारी योजना शोधण्यासाठी वापरली जाईल.\n\n"
                "• आम्ही कोणताही आधार क्रमांक, बँक तपशील किंवा पासवर्ड विचारत नाही.\n"
                "• आपण कधीही आपला डेटा पूर्णपणे हटवू ('/reset') शकता.\n\n"
                "आपण आपली माहिती जतन करण्यास संमती देता का?"
            )
        else:
            return (
                "🛡️ **Privacy & Consent (DPDP Act, 2023):**\n\n"
                "Under India's Digital Personal Data Protection Act, your basic demographic details "
                "(age, state, occupation) are used exclusively to determine government scheme eligibility.\n\n"
                "• Zero collection of Aadhaar numbers, OTPs, or financial credentials.\n"
                "• Full sovereignty: update or permanently delete your data anytime via `/reset`.\n\n"
                "Do you consent to saving your assessment profile?"
            )
