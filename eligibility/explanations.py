"""
Friendly, localized explanations for Scheme Eligibility Decisions.
Available in English, Hindi, and Marathi.
Never promises approval and clearly highlights what needs verification.
"""

from typing import Dict, Any
from database.models import SchemeEligibilityReport


class EligibilityExplainer:
    @staticmethod
    def explain_report(report: SchemeEligibilityReport, language: str = "en") -> str:
        status = report.overall_status
        name = report.scheme_name

        if language == "hi":
            return EligibilityExplainer._explain_hi(report)
        elif language == "mr":
            return EligibilityExplainer._explain_mr(report)
        else:
            return EligibilityExplainer._explain_en(report)

    @staticmethod
    def _explain_en(report: SchemeEligibilityReport) -> str:
        s = report.overall_status
        lines = []
        if s == "ELIGIBLE":
            lines.append(f"✅ **You appear Eligible for {report.scheme_name}!**")
            lines.append("Based on the details in your citizen profile, you satisfy all encoded mandatory requirements.")
        elif s == "NOT_ELIGIBLE":
            lines.append(f"❌ **You do not currently qualify for {report.scheme_name}.**")
            lines.append("One or more mandatory official conditions were not satisfied based on your profile.")
        else:
            lines.append(f"⚠️ **{report.scheme_name} Requires Further Verification.**")
            lines.append("We need a few more details to confirm whether you qualify, or this scheme has evolving guidelines.")

        if report.missing_fields:
            missing_str = ", ".join([f.replace('_', ' ') for f in report.missing_fields])
            lines.append(f"\nℹ️ *Information to verify:* {missing_str}")

        lines.append("\n**Rule Evaluation Summary:**")
        for r in report.evaluated_rules:
            icon = "✅" if r.status == "PASS" else ("❌" if r.status == "FAIL" else "❓")
            lines.append(f"- {icon} **{r.rule}**: {r.explanation} (Expected: {r.expected_value}, Your input: {r.user_value})")

        lines.append(f"\n💡 *Benefit:* {report.benefit_summary}")
        lines.append("\n> **Important Disclaimer:** Civicsaathi evaluates published guidelines deterministically. Final enrollment is subject to official Government scrutiny.")
        return "\n".join(lines)

    @staticmethod
    def _explain_hi(report: SchemeEligibilityReport) -> str:
        s = report.overall_status
        lines = []
        if s == "ELIGIBLE":
            lines.append(f"✅ **आप {report.scheme_name} के लिए पात्र प्रतीत होते हैं!**")
            lines.append("आपकी प्रोफाइल की जानकारी के अनुसार आप सभी आवश्यक शर्तें पूरी करते हैं।")
        elif s == "NOT_ELIGIBLE":
            lines.append(f"❌ **आप वर्तमान में {report.scheme_name} के लिए पात्र नहीं हैं।**")
            lines.append("सरकारी नियमों के अनुसार एक या अधिक अनिवार्य शर्तें पूरी नहीं हुईं।")
        else:
            lines.append(f"⚠️ **{report.scheme_name} के लिए अतिरिक्त जानकारी की आवश्यकता है।**")
            lines.append("पात्रता की पुष्टि के लिए कुछ विवरणों की पुष्टि करना ज़रूरी है।")

        if report.missing_fields:
            missing_str = ", ".join([f.replace('_', ' ') for f in report.missing_fields])
            lines.append(f"\nℹ️ *पुष्टि हेतु आवश्यक जानकारी:* {missing_str}")

        lines.append("\n**नियमों की जाँच का विवरण:**")
        for r in report.evaluated_rules:
            icon = "✅" if r.status == "PASS" else ("❌" if r.status == "FAIL" else "❓")
            lines.append(f"- {icon} **{r.rule}**: {r.explanation} (आवश्यकता: {r.expected_value}, आपका विवरण: {r.user_value})")

        lines.append(f"\n💡 *लाभ:* {report.benefit_summary}")
        lines.append("\n> **महत्वपूर्ण सूचना:** नागरिक साथी प्रकाशित सरकारी नियमों के आधार पर मार्गदर्शन देता है। अंतिम स्वीकृति संबंधित सरकारी विभाग द्वारा ही दी जाती है।")
        return "\n".join(lines)

    @staticmethod
    def _explain_mr(report: SchemeEligibilityReport) -> str:
        s = report.overall_status
        lines = []
        if s == "ELIGIBLE":
            lines.append(f"✅ **आपण {report.scheme_name} साठी पात्र दिसत आहात!**")
            lines.append("आपल्या प्रोफाइलनुसार आपण सर्व अनिवार्य अटी पूर्ण करत आहात.")
        elif s == "NOT_ELIGIBLE":
            lines.append(f"❌ **आपण सध्या {report.scheme_name} साठी पात्र नाही.**")
            lines.append("शासकीय नियमांनुसार एक किंवा अधिक अटी पूर्ण होत नाहीत.")
        else:
            lines.append(f"⚠️ **{report.scheme_name} साठी अधिक पडताळणी आवश्यक आहे.**")
            lines.append("पात्रता निश्चित करण्यासाठी काही अधिक माहितीची पडताळणी करणे गरजेचे आहे.")

        if report.missing_fields:
            missing_str = ", ".join([f.replace('_', ' ') for f in report.missing_fields])
            lines.append(f"\nℹ️ *पडताळणीसाठी आवश्यक माहिती:* {missing_str}")

        lines.append("\n**अटी पडताळणी तपशील:**")
        for r in report.evaluated_rules:
            icon = "✅" if r.status == "PASS" else ("❌" if r.status == "FAIL" else "❓")
            lines.append(f"- {icon} **{r.rule}**: {r.explanation} (अपेक्षित: {r.expected_value}, आपली माहिती: {r.user_value})")

        lines.append(f"\n💡 *योजनेचा लाभ:* {report.benefit_summary}")
        lines.append("\n> **महत्त्वाची नोंद:** नागरीक साथी अधिकृत नियमांनुसार मार्गदर्शन करतो. अंतिम मान्यता शासकीय तपासणीनंतरच दिली जाते.")
        return "\n".join(lines)
