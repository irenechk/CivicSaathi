"""
Groq API Integration Service for Civicsaathi.
Provides high-speed LLM inference and Multilingual Whisper Audio Transcription.
Features 100% graceful fallback to local deterministic RAG if the API is offline or unconfigured.
"""

import os
import io
import json
import logging
from typing import Optional, Dict, Any, List
import aiohttp

logger = logging.getLogger(__name__)

DEFAULT_GROQ_CHAT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
DEFAULT_GROQ_AUDIO_MODEL = os.getenv("GROQ_AUDIO_MODEL", "whisper-large-v3")


class GroqService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip() if api_key is None else api_key.strip()
        self.base_url = "https://api.groq.com/openai/v1"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("gsk_"))

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "voice.ogg",
        language: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """
        Transcribes speech using Groq Whisper (whisper-large-v3).
        Supports English, Hindi, and Marathi automatically.
        """
        if not self.is_configured:
            logger.warning("Groq API key not configured for audio transcription.")
            return None

        model_name = model or DEFAULT_GROQ_AUDIO_MODEL
        url = f"{self.base_url}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            data = aiohttp.FormData()
            data.add_field("file", audio_bytes, filename=filename, content_type="audio/ogg")
            data.add_field("model", model_name)
            data.add_field("response_format", "json")
            if language:
                data.add_field("language", language)

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        text = res_json.get("text", "").strip()
                        logger.info(f"Groq Whisper transcription success ({len(text)} chars)")
                        return text
                    else:
                        err_text = await resp.text()
                        logger.error(f"Groq Whisper transcription error (HTTP {resp.status}): {err_text}")
                        return None
        except Exception as e:
            logger.error(f"Groq Whisper transcription exception: {e}", exc_info=True)
            return None

    async def synthesize_scheme_answer(
        self,
        query: str,
        retrieved_passages: List[Dict[str, Any]],
        language: str = "en",
        profile: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Synthesizes an evidence-grounded answer using Groq LLM.
        Strictly enforces official citations and zero credential collection.
        """
        if not self.is_configured or not retrieved_passages:
            return None

        model_name = model or DEFAULT_GROQ_CHAT_MODEL
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Build context from retrieved passages
        evidence_blocks = []
        citations = []
        for i, p in enumerate(retrieved_passages[:3], 1):
            meta = p.get("metadata", {})
            evidence_blocks.append(
                f"[Source {i}: {meta.get('scheme_name', 'Scheme')}]\n{p.get('text', '')}"
            )
            if meta.get("official_url"):
                citations.append({
                    "scheme_name": meta.get("scheme_name", "Scheme"),
                    "source_url": meta.get("official_url", "https://myscheme.gov.in"),
                })

        evidence_text = "\n\n".join(evidence_blocks)

        # Profile context
        prof_info = "None provided"
        if profile:
            prof_info = (
                f"State: {getattr(profile, 'state', 'All India')}, "
                f"Age: {getattr(profile, 'age', 'N/A')}, "
                f"Gender: {getattr(profile, 'gender', 'N/A')}, "
                f"Occupation: {getattr(profile, 'occupation', 'N/A')}, "
                f"Income: ₹{getattr(profile, 'annual_family_income', 0):,.0f}, "
                f"Category: {getattr(profile, 'category', 'General')}"
            )

        lang_instruction = {
            "hi": "उत्तर पूरी तरह शुद्ध एवं सरल हिंदी में दें। आवश्यक तकनीकी शब्द या योजना नाम कोष्ठक में अंग्रेजी में रख सकते हैं।",
            "mr": "उत्तर संपूर्णपणे सुलभ आणि स्पष्ट मराठीत द्या. योजनांची नावे कंसात ठेवू शकता.",
            "en": "Answer in clear, concise, trustworthy Indian English.",
        }.get(language, "Answer in English.")

        system_prompt = (
            "You are Civicsaathi (नागरिक साथी), an AI government scheme intelligence assistant for Indian citizens.\n"
            "STRICT RULES:\n"
            "1. Ground all facts, eligibility, benefits, and documents STRICTLY on the provided Verified Evidence.\n"
            "2. Never fabricate eligibility conditions, disbursement amounts, or websites.\n"
            "3. If evidence is missing or uncertain, explicitly tell the citizen that official verification is required.\n"
            "4. Never ask for Aadhaar numbers, OTPs, bank passwords, or debit card pins.\n"
            f"5. Language: {lang_instruction}\n"
            "6. Keep the answer structured, citizen-friendly, and concise (bullet points for steps/documents)."
        )

        user_content = (
            f"Verified Evidence:\n{evidence_text}\n\n"
            f"Citizen Profile:\n{prof_info}\n\n"
            f"Citizen Query: {query}"
        )

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": 600,
            "temperature": 0.2,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        choices = res_json.get("choices", [])
                        if choices:
                            answer_text = choices[0].get("message", {}).get("content", "").strip()
                            if answer_text:
                                return {
                                    "answer": answer_text,
                                    "citations": citations,
                                    "confidence": 0.95,
                                    "source": "groq_llm",
                                }
                    else:
                        err_text = await resp.text()
                        logger.warning(f"Groq LLM call returned HTTP {resp.status}: {err_text}")
                        return None
        except Exception as e:
            logger.warning(f"Groq LLM call exception: {e}")
            return None

        return None
