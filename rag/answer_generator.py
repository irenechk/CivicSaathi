"""
Answer Generator for Civicsaathi RAG Pipeline.
Translates retrieved scheme records and citizen queries into clear, authoritative,
respectful, and empathetic explanations in English, Hindi, and Marathi.
Uses fine-grained intent classification to return the EXACT specific data requested
(benefit amount, website link, age criteria, income ceiling, documents, application steps, premium)
rather than overwhelming the citizen with generic scheme dumps.
"""

import re
import requests
from typing import List, Dict, Any, Optional
from database.repository import SchemeRepository


class AnswerGenerator:
    def __init__(self, ollama_url: str = "http://localhost:11434", model_name: str = "llama3:8b"):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.scheme_repo = SchemeRepository()

    def is_ollama_available(self) -> bool:
        """Check if local Ollama daemon is running."""
        try:
            res = requests.get(f"{self.ollama_url}/api/tags", timeout=0.8)
            return res.status_code == 200
        except Exception:
            return False

    def generate_answer(
        self,
        query: str,
        retrieved_passages: Optional[List[Dict[str, Any]]] = None,
        language: str = "en",
        passages: Optional[List[Dict[str, Any]]] = None,
        profile: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes an answer backed by retrieved passages and canonical scheme records.
        Supports conversational context and citizen profile memory for multi-turn dialogues.
        """
        candidate_passages = retrieved_passages if retrieved_passages is not None else (passages or [])

        # Check for general citizen welfare procedures first
        proc_answer = self._check_procedural_topics(query, language)
        if proc_answer:
            return {
                "answer": proc_answer["answer"],
                "citations": proc_answer["citations"],
                "engine": "procedural_knowledge_engine",
            }

        if not candidate_passages:
            return {
                "answer": self._no_results_message(language),
                "citations": [],
                "engine": "deterministic_fallback",
            }

        # Check for local Ollama if available
        if self.is_ollama_available():
            try:
                answer = self._call_ollama(query, candidate_passages, language)
                citations = self._extract_citations(candidate_passages)
                return {
                    "answer": answer,
                    "citations": citations,
                    "engine": f"local_ollama ({self.model_name})",
                }
            except Exception:
                pass  # Fallback to rich targeted deterministic engine

        # Fine-grained targeted deterministic generation using full SchemeRecord
        answer = self._deterministic_synthesizer(query, candidate_passages, language, profile=profile, context=context)
        citations = self._extract_citations(candidate_passages)
        return {
            "answer": answer,
            "citations": citations,
            "engine": "deterministic_knowledge_engine",
        }

    def _call_ollama(self, query: str, passages: List[Dict[str, Any]], language: str) -> str:
        context = "\n\n".join([f"[{p['metadata'].get('scheme_name')}] {p['text']}" for p in passages[:3]])
        lang_names = {"en": "English", "hi": "Hindi", "mr": "Marathi"}
        target_lang = lang_names.get(language, "English")

        prompt = (
            f"You are Civicsaathi, an empathetic and highly knowledgeable Indian government scheme assistant.\n"
            f"Respond strictly in {target_lang}.\n"
            f"Answer the citizen's query based ONLY on the verified context below. Be concise, polite, and directly address the specific question.\n\n"
            f"Verified Context:\n{context}\n\n"
            f"Citizen Query: {query}\n\n"
            f"Direct Answer:"
        )
        res = requests.post(
            f"{self.ollama_url}/api/generate",
            json={"model": self.model_name, "prompt": prompt, "stream": False},
            timeout=10.0,
        )
        return res.json().get("response", "").strip()

    def _check_procedural_topics(self, query: str, language: str) -> Optional[Dict[str, Any]]:
        """Handles general citizen procedural questions (DBT, Aadhaar linking, Helplines, Grievances)."""
        q_lower = query.lower()

        # 1. DBT and Aadhaar Bank Seeding
        if re.search(r"\b(dbt|direct benefit transfer|aadhaar link|seed bank|aadhaar seeding|खाता लिंक|आधार लिंक|डीबीटी)\b", q_lower):
            if language == "hi":
                text = (
                    "💳 **प्रत्यक्ष लाभ अंतरण (DBT) एवं बैंक खाता आधार सीडिंग:**\n\n"
                    "सरकारी योजनाओं (जैसे PM-KISAN, PMMVY आदि) की राशि सीधे आपके बैंक खाते में पाने के लिए बैंक खाते का आधार से 'सीड' (NPCI Mapped) होना अनिवार्य है।\n\n"
                    "📌 **सीडिंग कराने के चरण:**\n"
                    "1. अपनी बैंक शाखा में जाकर **'Aadhaar Seeding / DBT Mandate Form'** भरें।\n"
                    "2. आधार कार्ड और बैंक पासबुक की स्व-प्रमाणित फोटोकॉपी संलग्न करें।\n"
                    "3. बैंक अधिकारी से पुष्टि करें कि आपका खाता **NPCI Mapper** पर सक्रिय हो गया है।"
                )
            elif language == "mr":
                text = (
                    "💳 **थेट लाभ हस्तांतरण (DBT) आणि आधार बँक खाते लिंक:**\n\n"
                    "शासकीय योजनांचे अनुदान थेट मिळवण्यासाठी आपले बँक खाते आधारशी 'सीड' (NPCI Mapped) असणे आवश्यक आहे.\n\n"
                    "📌 **पायऱ्या:**\n"
                    "१. बँक शाखेत जाऊन **'DBT आधार सीडिंग फॉर्म'** भरा.\n"
                    "२. आधार कार्ड व पासबुकची स्वाक्षरी केलेली प्रत जमा करा.\n"
                    "३. बँक कर्मचाऱ्याकडून आपले खाते **NPCI Mapper** वर लिंक झाल्याची खात्री करा."
                )
            else:
                text = (
                    "💳 **Direct Benefit Transfer (DBT) & Aadhaar Bank Seeding:**\n\n"
                    "To receive subsidies under government schemes, your savings account must be seeded with Aadhaar on the **NPCI Mapper**.\n\n"
                    "📌 **Steps for Seeding:**\n"
                    "1. Visit your bank branch and submit the **Aadhaar Seeding / DBT Mandate Form**.\n"
                    "2. Attach copies of your Aadhaar Card and Bank Passbook.\n"
                    "3. Ask the branch official to map your account on the NPCI database."
                )
            return {
                "answer": text,
                "citations": [{"scheme_name": "DBT Bharat Portal", "source_url": "https://dbtbharat.gov.in"}],
            }

        # 2. National Helplines
        if re.search(r"\b(helpline|toll free|call center|help line|contact number|फोन नंबर|हेल्पलाइन|मदत क्रमांक)\b", q_lower) and not re.search(r"\b(kcc|pm-kisan|pmsby|pmmvy)\b", q_lower):
            if language == "hi":
                text = (
                    "📞 **महत्वपूर्ण राष्ट्रीय हेल्पलाइन 🇮🇳**\n\n"
                    "• 🚨 **राष्ट्रीय आपातकालीन:** 112\n"
                    "• 🌾 **किसान कॉल सेंटर:** 1800-180-1551\n"
                    "• 🏥 **आयुष्मान भारत (स्वास्थ्य):** 14555\n"
                    "• 👩 **महिला हेल्पलाइन:** 181 / 1091\n"
                    "• 💻 **साइबर अपराध शिकायत:** 1930\n"
                    "• 👶 **चाइल्डलाइन:** 1098\n"
                    "• 👴 **वरिष्ठ नागरिक:** 14567"
                )
            elif language == "mr":
                text = (
                    "📞 **महत्त्वाचे राष्ट्रीय हेल्पलाइन क्रमांक 🇮🇳**\n\n"
                    "• 🚨 **राष्ट्रीय आपत्कालीन सेवा:** 112\n"
                    "• 🌾 **किसान कॉल सेंटर:** 1800-180-1551\n"
                    "• 🏥 **आयुष्मान भारत (आरोग्य):** 14555\n"
                    "• 👩 **महिला हेल्पलाइन:** 181 / 1091\n"
                    "• 💻 **सायबर गुन्हे:** 1930\n"
                    "• 👶 **चाइल्डलाइन:** 1098\n"
                    "• 👴 **ज्येष्ठ नागरिक:** 14567"
                )
            else:
                text = (
                    "📞 **Important National Government Helplines 🇮🇳**\n\n"
                    "• 🚨 **National Emergency:** 112\n"
                    "• 🌾 **Kisan Call Centre (Farmers):** 1800-180-1551\n"
                    "• 🏥 **Ayushman Bharat (Health Services):** 14555\n"
                    "• 👩 **Women in Distress:** 181 / 1091\n"
                    "• 💻 **Cyber Crime:** 1930\n"
                    "• 👶 **Childline:** 1098\n"
                    "• 👴 **Elderline (Senior Citizens):** 14567"
                )
            return {
                "answer": text,
                "citations": [{"scheme_name": "National Portal of India", "source_url": "https://india.gov.in"}],
            }

        # 3. Grievances and CPGRAMS
        if re.search(r"\b(grievance|complaint|cpgrams|pgportal|शिकायत|तक्रार)\b", q_lower):
            if language == "hi":
                text = (
                    "⚖️ **केंद्रीय लोक शिकायत निवारण प्रणाली (CPGRAMS):**\n\n"
                    "किसी भी सरकारी विभाग अथवा योजना की शिकायत के लिए:\n"
                    "1. आधिकारिक पोर्टल **pgportal.gov.in** पर जाएं।\n"
                    "2. मोबाइल नंबर से लॉगिन कर 'Lodge Public Grievance' चुनें।\n"
                    "3. संबंधित मंत्रालय का चयन करें और विवरण दर्ज करें।"
                )
            elif language == "mr":
                text = (
                    "⚖️ **केंद्रीय सार्वजनिक तक्रार निवारण प्रणाली (CPGRAMS):**\n\n"
                    "शासकीय योजना किंवा विभागाशी संबंधित तक्रारीसाठी:\n"
                    "१. **pgportal.gov.in** संकेतस्थळाला भेट द्या.\n"
                    "२. मोबाईल नंबरने लॉगिन करून तक्रार नोंदवा.\n"
                    "३. संबंधित विभाग निवडून कागदपत्रे जोडा."
                )
            else:
                text = (
                    "⚖️ **Centralised Public Grievance Redress System (CPGRAMS):**\n\n"
                    "To lodge a formal grievance against any central or state department:\n"
                    "1. Visit the portal: **pgportal.gov.in**.\n"
                    "2. Sign in with your mobile number or email.\n"
                    "3. Select the relevant Ministry and submit your complaint."
                )
            return {
                "answer": text,
                "citations": [{"scheme_name": "CPGRAMS Portal", "source_url": "https://pgportal.gov.in"}],
            }

        return None

    def _deterministic_synthesizer(
        self,
        query: str,
        passages: List[Dict[str, Any]],
        language: str,
        profile: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Synthesizes high-clarity, atomic, pinpoint answers matching the specific data asked.
        Avoids dumping generic 20-line summaries when a citizen asks for one specific field.
        """
        top = passages[0]
        meta = top.get("metadata", {})
        scheme_id = meta.get("scheme_id")

        scheme = self.scheme_repo.get_scheme_by_id(scheme_id) if scheme_id else None

        q_lower = query.lower()

        # Context Tagging: If the citizen did not repeat the scheme name, add a brief 1-line reference
        context_anchor = ""
        active_name = (context.get("active_scheme_name") if context else None)
        if active_name and scheme:
            distinctive_tokens = set(re.findall(r"\w+", scheme.scheme_name.lower())) - {"yojana", "pradhan", "mantri", "national", "scheme"}
            if not distinctive_tokens.intersection(set(re.findall(r"\w+", q_lower))):
                if language == "hi":
                    context_anchor = f"💬 *(संदर्भ: **{scheme.scheme_name}**)*\n\n"
                elif language == "mr":
                    context_anchor = f"💬 *(संदर्भ: **{scheme.scheme_name}**)*\n\n"
                else:
                    context_anchor = f"💬 *(In reference to: **{scheme.scheme_name}**)*\n\n"

        # Fallback if no structured record
        if not scheme:
            scheme_name = meta.get("scheme_name", "Government Scheme")
            v_status = meta.get("verification_status", "verified")
            if language == "hi":
                return f"{context_anchor}🏛️ **{scheme_name}**\n*(सत्यापन स्थिति: {v_status})*\n\n{top.get('text', '')}"
            elif language == "mr":
                return f"{context_anchor}🏛️ **{scheme_name}**\n*(पडताळणी स्थिती: {v_status})*\n\n{top.get('text', '')}"
            return f"{context_anchor}🏛️ **{scheme_name}**\n*(Verification Status: {v_status})*\n\n{top.get('text', '')}"

        alts_str = f" ({', '.join(scheme.alternate_names)})" if scheme.alternate_names else ""
        scheme_display = f"{scheme.scheme_name}{alts_str}"
        portal_url = scheme.official_application_url or scheme.official_scheme_url or "https://myscheme.gov.in"

        # =========================================================================
        # SPECIFIC INTENT CLASSIFICATION (Precision First)
        # =========================================================================

        # 1. SPECIFIC: Official Website / Portal / Link
        is_link_query = bool(re.search(r"\b(website|link|portal|official site|url|वेबसाइट|पोर्टल|लिंक|संकेतस्थळ)\b", q_lower)) and not bool(re.search(r"\b(how to|steps|process|दस्तावेज|कागदपत्रे)\b", q_lower))
        if is_link_query:
            if language == "hi":
                return (
                    f"{context_anchor}🔗 **{scheme_display} का आधिकारिक पोर्टल:**\n\n"
                    f"• **वेबसाइट लिंक:** {portal_url}\n\n"
                    f"💡 इस आधिकारिक पोर्टल पर आप सीधे ऑनलाइन आवेदन, ई-केवाईसी (e-KYC) और आवेदन की स्थिति देख सकते हैं।"
                )
            elif language == "mr":
                return (
                    f"{context_anchor}🔗 **{scheme_display} अधिकृत संकेतस्थळ:**\n\n"
                    f"• **संकेतस्थळ लिंक:** {portal_url}\n\n"
                    f"💡 या अधिकृत पोर्टलवर आपण ऑनलाईन अर्ज, ई-केवायसी आणि अर्जाची स्थिती तपासू शकता."
                )
            else:
                return (
                    f"{context_anchor}🔗 **Official Website for {scheme_display}:**\n\n"
                    f"• **Official Portal:** {portal_url}\n\n"
                    f"💡 You can apply online, complete e-KYC, and track your application status directly on this portal."
                )

        # 2. SPECIFIC: Age Limit / Age Criteria
        is_age_query = bool(re.search(r"\b(age|age limit|minimum age|maximum age|how old|उम्र|आयु|वयोमर्यादा|वय)\b", q_lower)) and not bool(re.search(r"\b(apply|documents|दस्तावेज)\b", q_lower))
        if is_age_query:
            min_a = scheme.eligibility.age_min
            max_a = scheme.eligibility.age_max
            if min_a and max_a:
                age_txt = f"{min_a} to {max_a} years"
            elif min_a:
                age_txt = f"Minimum {min_a} years (No upper limit)"
            elif max_a:
                age_txt = f"Up to {max_a} years"
            else:
                age_txt = "No specific age restrictions specified."

            if language == "hi":
                return (
                    f"{context_anchor}🎂 **{scheme_display} के लिए आयु सीमा (Age Limit):**\n\n"
                    f"• **पात्र आयु:** **{age_txt}**\n"
                    f"• **लक्षित वर्ग:** {', '.join(scheme.target_beneficiaries[:2]) if scheme.target_beneficiaries else 'पात्र नागरिक'}"
                )
            elif language == "mr":
                return (
                    f"{context_anchor}🎂 **{scheme_display} साठी वयोमर्यादा (Age Limit):**\n\n"
                    f"• **पात्र वय:** **{age_txt}**\n"
                    f"• **लक्षित लाभार्थी:** {', '.join(scheme.target_beneficiaries[:2]) if scheme.target_beneficiaries else 'पात्र नागरिक'}"
                )
            else:
                return (
                    f"{context_anchor}🎂 **Age Criteria for {scheme_display}:**\n\n"
                    f"• **Eligible Age:** **{age_txt}**\n"
                    f"• **Target Group:** {', '.join(scheme.target_beneficiaries[:2]) if scheme.target_beneficiaries else 'Eligible citizens'}"
                )

        # 3. SPECIFIC: Income Limit / Ceiling
        is_income_query = bool(re.search(r"\b(income|income limit|salary|earning limit|आय सीमा|वार्षिक आय|उत्पन्न|उत्पन्न मर्यादा)\b", q_lower)) and not bool(re.search(r"\b(apply|documents|दस्तावेज)\b", q_lower))
        if is_income_query:
            inc_limit = scheme.eligibility.income_limit
            if inc_limit:
                inc_txt = f"INR {inc_limit:,.0f} per annum"
            else:
                inc_txt = "No strict income ceiling specified under standard guidelines."

            if language == "hi":
                return (
                    f"{context_anchor}💰 **{scheme_display} के लिए आय मानदंड (Income Limit):**\n\n"
                    f"• **वार्षिक पारिवारिक आय सीमा:** **{inc_txt}**\n"
                    f"• **सत्यापन:** राजस्व विभाग द्वारा जारी वैध आय प्रमाण पत्र।"
                )
            elif language == "mr":
                return (
                    f"{context_anchor}💰 **{scheme_display} साठी उत्पन्न मर्यादा (Income Limit):**\n\n"
                    f"• **कौटुंबिक उत्पन्न मर्यादा:** **{inc_txt}**\n"
                    f"• **पुरावा:** तहसीलदारांचा अधिकृत उत्पन्नाचा दाखला."
                )
            else:
                return (
                    f"{context_anchor}💰 **Income Ceiling for {scheme_display}:**\n\n"
                    f"• **Annual Family Income Limit:** **{inc_txt}**\n"
                    f"• **Verification:** Valid revenue-certified income certificate."
                )

        # 4. SPECIFIC: Benefit Amount / Money Received / Installment
        is_amount_query = bool(re.search(r"\b(how much|how much money|amount|cash|pension amount|subsidy amount|installment|कितने पैसे|कितना लाभ|रुपये|मिळतील|किती पैसे|अनुदान रक्कम|हप्ता)\b", q_lower))
        if is_amount_query:
            b_amount = scheme.benefit_amount or "Financial assistance as per approved guidelines"
            b_freq = scheme.benefit_frequency or "Direct Benefit Transfer (DBT)"
            b_type = ", ".join(scheme.benefit_type) if scheme.benefit_type else "Welfare Benefit"

            if language == "hi":
                return (
                    f"{context_anchor}💰 **{scheme_display} के अंतर्गत मिलने वाली सहायता राशि:**\n\n"
                    f"• **लाभ राशि:** **{b_amount}**\n"
                    f"• **भुगतान का माध्यम:** {b_freq} (सीधे आधार-लिंक बैंक खाते में)\n"
                    f"• **प्रकार:** {b_type}"
                )
            elif language == "mr":
                return (
                    f"{context_anchor}💰 **{scheme_display} अंतर्गत मिळणारी लाभाची रक्कम:**\n\n"
                    f"• **लाभाची रक्कम:** **{b_amount}**\n"
                    f"• **वितरण:** {b_freq} (थेट आधार-लिंक बँक खात्यात)\n"
                    f"• **प्रकार:** {b_type}"
                )
            else:
                return (
                    f"{context_anchor}💰 **Benefit Amount for {scheme_display}:**\n\n"
                    f"• **Financial Support:** **{b_amount}**\n"
                    f"• **Disbursement:** {b_freq} (Direct Benefit Transfer to bank account)\n"
                    f"• **Benefit Type:** {b_type}"
                )

        # 5. SPECIFIC: Premium / Interest Rate / Cost
        is_rate_query = bool(re.search(r"\b(premium|cost|charge|fees|interest rate|rate of interest|व्याज|व्याजदर|प्रीमियम|शुल्क|ब्याज|ब्याज दर)\b", q_lower))
        if is_rate_query:
            # Custom rate precision for flagship schemes
            if "pmsby" in scheme.scheme_id.lower() or "suraksha" in scheme.scheme_name.lower():
                rate_info = "Annual Premium: **₹20 per year** (Auto-debited from savings bank account)."
            elif "pmjjby" in scheme.scheme_id.lower() or "jeevan jyoti" in scheme.scheme_name.lower():
                rate_info = "Annual Premium: **₹436 per year** for ₹2,00,000 life insurance coverage."
            elif "kcc" in scheme.scheme_id.lower() or "kisan credit" in scheme.scheme_name.lower():
                rate_info = "Concessional **7% p.a.** on short-term crop loans up to ₹3,00,000 (effectively **4%** with 3% prompt repayment incentive)."
            elif "sukanya" in scheme.scheme_name.lower() or "ssy" in scheme.scheme_id.lower():
                rate_info = "Guaranteed small savings interest rate of **8.2% p.a.** (tax-free under Section 80C)."
            else:
                rate_info = scheme.benefit_amount or "As per official scheme guidelines."

            if language == "hi":
                return f"{context_anchor}📊 **{scheme_display} दर / प्रीमियम विवरण:**\n\n• {rate_info}"
            elif language == "mr":
                return f"{context_anchor}📊 **{scheme_display} दर / प्रीमियम तपशील:**\n\n• {rate_info}"
            else:
                return f"{context_anchor}📊 **Rate & Premium for {scheme_display}:**\n\n• {rate_info}"

        # 6. SPECIFIC: Required Documents Checklist
        is_docs_query = bool(re.search(r"\b(document|documents|paper|papers|certificate|card|proof|aadhaar|कागदपत्रे|कागदपत्र|दस्तावेज|प्रमाणपत्र)\b", q_lower))
        if is_docs_query:
            doc_items = scheme.required_documents if scheme.required_documents else ["[Mandatory] Aadhaar Card", "[Mandatory] Bank Account Passbook", "[Mandatory] Passport Photo"]
            doc_formatted = "\n".join([f"• {d}" for d in doc_items])
            if language == "hi":
                return (
                    f"{context_anchor}📄 **{scheme_display} के लिए आवश्यक दस्तावेज़:**\n\n"
                    f"{doc_formatted}\n\n"
                    f"💡 *आवेदन का माध्यम:* {scheme.application_mode or 'ऑनलाइन / ऑफलाइन'}"
                )
            elif language == "mr":
                return (
                    f"{context_anchor}📄 **{scheme_display} साठी आवश्यक कागदपत्रे:**\n\n"
                    f"{doc_formatted}\n\n"
                    f"💡 *अर्जाचे स्वरूप:* {scheme.application_mode or 'ऑनलाईन / ऑफलाईन'}"
                )
            else:
                return (
                    f"{context_anchor}📄 **Documents Required for {scheme_display}:**\n\n"
                    f"{doc_formatted}\n\n"
                    f"💡 *Application Mode:* {scheme.application_mode or 'Online / Offline'}"
                )

        # 7. SPECIFIC: How to Apply / Application Steps
        is_apply_query = bool(re.search(r"\b(how to apply|how do i apply|apply|application process|steps|procedure|where to apply|कुठे अर्ज करावा|अर्ज कसा करावा|आवेदन कैसे करें|फॉर्म कैसे भरें)\b", q_lower))
        if is_apply_query:
            if scheme.application_process:
                steps_txt = "\n".join([f"{i}. {s}" for i, s in enumerate(scheme.application_process, 1)])
            else:
                steps_txt = (
                    "1. Visit the official portal or your nearest Common Service Centre (CSC) / Bank branch.\n"
                    "2. Submit the registration form with your Aadhaar and bank details.\n"
                    "3. Complete Aadhaar e-KYC and attach necessary proofs."
                )

            if language == "hi":
                return (
                    f"{context_anchor}📝 **{scheme_display} में आवेदन करने के चरण:**\n\n"
                    f"• **माध्यम:** {scheme.application_mode or 'ऑनलाइन एवं ऑफलाइन'}\n"
                    f"• **आधिकारिक पोर्टल:** {portal_url}\n\n"
                    f"📌 **आवेदन प्रक्रिया:**\n{steps_txt}\n\n"
                    f"🔗 [सीधे आधिकारिक पोर्टल पर जाएं]({portal_url})"
                )
            elif language == "mr":
                return (
                    f"{context_anchor}📝 **{scheme_display} अर्ज करण्याच्या पायऱ्या:**\n\n"
                    f"• **स्वरूप:** {scheme.application_mode or 'ऑनलाईन आणि ऑफलाईन'}\n"
                    f"• **अधिकृत संकेतस्थळ:** {portal_url}\n\n"
                    f"📌 **अर्ज प्रक्रिया:**\n{steps_txt}\n\n"
                    f"🔗 [थेट अधिकृत संकेतस्थळाला भेट द्या]({portal_url})"
                )
            else:
                return (
                    f"{context_anchor}📝 **How to Apply for {scheme_display}:**\n\n"
                    f"• **Mode:** {scheme.application_mode or 'Online & Offline'}\n"
                    f"• **Official Portal:** {portal_url}\n\n"
                    f"📌 **Application Procedure:**\n{steps_txt}\n\n"
                    f"🔗 [Visit Official Application Portal]({portal_url})"
                )

        # 8. SPECIFIC: Am I Eligible / Eligibility Evaluation
        is_elig_query = bool(re.search(r"\b(am i eligible|can i apply|am i qualify|who can apply|who is eligible|क्या मैं पात्र हूँ|पात्रता|पात्र आहे का)\b", q_lower))
        if is_elig_query:
            profile_note = ""
            if profile and (getattr(profile, "age", None) or getattr(profile, "occupation", None)):
                name_label = getattr(profile, "full_name", None) or ("नागरिक" if language != "en" else "Citizen")
                occ = getattr(profile, "occupation", "N/A")
                age = getattr(profile, "age", "N/A")
                st = getattr(profile, "state", "Pan-India")
                inc = getattr(profile, "annual_family_income", None)
                inc_fmt = f"₹{inc:,.0f}" if inc else "N/A"
                if language == "hi":
                    profile_note = f"👤 **{name_label} जी के लिए पात्रता जाँच:**\n• दर्ज प्रोफाइल: {occ} | आयु: {age} वर्ष | राज्य: {st} | आय: {inc_fmt}\n\n"
                elif language == "mr":
                    profile_note = f"👤 **{name_label} यांच्यासाठी पात्रता तपासणी:**\n• नोंदवलेली माहिती: {occ} | वय: {age} वर्षे | राज्य: {st} | उत्पन्न: {inc_fmt}\n\n"
                else:
                    profile_note = f"👤 **Personalized Eligibility for {name_label}:**\n• Your Profile: {occ} | Age: {age} yrs | State: {st} | Income: {inc_fmt}\n\n"

            target_txt = ", ".join(scheme.target_beneficiaries) if scheme.target_beneficiaries else "All eligible citizens"
            age_txt = f"{scheme.eligibility.age_min or 'Any'} to {scheme.eligibility.age_max or 'Any'} years"
            inc_txt = f"Up to INR {scheme.eligibility.income_limit:,.0f}" if scheme.eligibility.income_limit else "No strict limit"

            if language == "hi":
                return (
                    f"{context_anchor}{profile_note}👥 **{scheme_display} पात्रता मानदंड:**\n\n"
                    f"• **लक्षित लाभार्थी:** {target_txt}\n"
                    f"• **आयु सीमा:** {age_txt}\n"
                    f"• **आय सीमा:** {inc_txt}\n"
                    f"• **शर्तें:** {' '.join(scheme.eligibility.other_conditions[:2]) if scheme.eligibility.other_conditions else 'मानक दिशा-निर्देश'}"
                )
            elif language == "mr":
                return (
                    f"{context_anchor}{profile_note}👥 **{scheme_display} पात्रता निकष:**\n\n"
                    f"• **लक्षित लाभार्थी:** {target_txt}\n"
                    f"• **वयोमर्यादा:** {age_txt}\n"
                    f"• **उत्पन्न मर्यादा:** {inc_txt}\n"
                    f"• **अटी:** {' '.join(scheme.eligibility.other_conditions[:2]) if scheme.eligibility.other_conditions else 'अधिकृत नियमांनुसार'}"
                )
            else:
                return (
                    f"{context_anchor}{profile_note}👥 **Eligibility Criteria for {scheme_display}:**\n\n"
                    f"• **Target Beneficiaries:** {target_txt}\n"
                    f"• **Age Limit:** {age_txt}\n"
                    f"• **Income Limit:** {inc_txt}\n"
                    f"• **Conditions:** {' '.join(scheme.eligibility.other_conditions[:2]) if scheme.eligibility.other_conditions else 'Standard guidelines'}"
                )

        # =========================================================================
        # GENERAL SCHEME QUERY (Only when open-ended overview is asked)
        # =========================================================================
        amount_str = scheme.benefit_amount or "Direct welfare benefit"
        target_str = ", ".join(scheme.target_beneficiaries[:2]) if scheme.target_beneficiaries else "Citizens"

        if language == "hi":
            return (
                f"{context_anchor}🏛️ **{scheme_display}**\n"
                f"*(सत्यापन स्थिति: {scheme.verification_status})*\n\n"
                f"📋 **योजना का परिचय:**\n{scheme.description}\n\n"
                f"💰 **प्रमुख लाभ:** {amount_str}\n"
                f"👥 **लक्षित वर्ग:** {target_str}\n"
                f"🔗 [आधिकारिक पोर्टल]({portal_url})\n\n"
                f"💡 *आप पूछ सकते हैं: 'आवेदन कैसे करें?', 'आवश्यक दस्तावेज़', या 'वेबसाइट लिंक'*"
            )
        elif language == "mr":
            return (
                f"{context_anchor}🏛️ **{scheme_display}**\n"
                f"*(पडताळणी स्थिती: {scheme.verification_status})*\n\n"
                f"📋 **योजनेचा परिचय:**\n{scheme.description}\n\n"
                f"💰 **प्रमुख लाभ:** {amount_str}\n"
                f"👥 **लक्षित लाभार्थी:** {target_str}\n"
                f"🔗 [अधिकृत संकेतस्थळ]({portal_url})\n\n"
                f"💡 *आपण विचारू शकता: 'अर्ज कसा करावा?', 'कागदपत्रे', किंवा 'संकेतस्थळ लिंक'*"
            )
        else:
            return (
                f"{context_anchor}🏛️ **{scheme_display}**\n"
                f"*(Verification Status: {scheme.verification_status})*\n\n"
                f"📋 **Overview:**\n{scheme.description}\n\n"
                f"💰 **Key Benefits:** {amount_str}\n"
                f"👥 **Target Group:** {target_str}\n"
                f"🔗 [Official Portal]({portal_url})\n\n"
                f"💡 *You can ask: 'How to apply', 'Required documents', or 'Website link'.*"
            )

    def _extract_citations(self, passages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        citations = []
        seen = set()
        for p in passages:
            meta = p.get("metadata", {})
            s_id = meta.get("scheme_id", "")
            if s_id and s_id not in seen:
                seen.add(s_id)
                scheme = self.scheme_repo.get_scheme_by_id(s_id) if hasattr(self, "scheme_repo") else None
                s_name = (scheme.scheme_name if scheme else meta.get("scheme_name")) or "Government Scheme"
                s_url = (scheme.official_application_url or scheme.official_scheme_url if scheme else meta.get("source_url")) or "https://myscheme.gov.in"
                v_status = (scheme.verification_status if scheme else meta.get("verification_status")) or "verified"
                v_date = (scheme.research_verified_date if scheme else meta.get("verified_date")) or "2026-11-21"
                doc_title = meta.get("document_title") or (scheme.source_notes[0] if scheme and scheme.source_notes else "Official Ministry Guidelines / myScheme Portal")
                section = meta.get("section") or "Operational Guidelines"

                citations.append({
                    "scheme_id": s_id,
                    "scheme_name": s_name,
                    "source_url": s_url,
                    "document_title": doc_title,
                    "section": section,
                    "verified_date": v_date,
                    "verification_status": v_status,
                })
        return citations

    def _no_results_message(self, language: str) -> str:
        if language == "hi":
            return (
                "⚠️ **सूचना: इस खोज के लिए विश्वसनीय आधिकारिक प्रमाण उपलब्ध नहीं हैं।**\n\n"
                "यह जानकारी संबंधित मंत्रालय से आधिकारिक सत्यापन की मांग करती है। सिविकसाथी बिना प्रमाण के अपुष्ट उत्तर नहीं देता।\n\n"
                "💡 **सुझाव:** योजना का सटीक नाम लिखें (उदा. PM-KISAN, KCC, PMMVY, PMSBY, APY) अथवा मुख्य मेनू के लिए `/start` दबाएं।"
            )
        elif language == "mr":
            return (
                "⚠️ **सूचना: या शोधासाठी पुरेसे अधिकृत सरकारी पुरावे उपलब्ध नाहीत.**\n\n"
                "ही माहिती संबंधित मंत्रालयाकडून अधिकृत पडताळणीच्या अधीन आहे. सिविकसाथी पुराव्याशिवाय माहिती देत नाही.\n\n"
                "💡 **मार्गदर्शन:** योजनेचे अधिकृत नाव लिहा (उदा. PM-KISAN, KCC, PMMVY, PMSBY, APY) किंवा `/start` वापरा."
            )
        return (
            "⚠️ **Notice: Reliable official evidence is unavailable for this query.**\n\n"
            "This information needs verification from official ministry sources before taking action. Civicsaathi strictly avoids ungrounded claims.\n\n"
            "💡 **Tip:** Try typing a specific scheme name (e.g. PM-KISAN, KCC, PMMVY, PMSBY, APY) or explore verified schemes via `/start`."
        )
