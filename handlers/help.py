"""
Help command handler and Smart Context-Aware Local RAG Question-Answering for Civicsaathi.
Processes citizen queries directly against the 30-scheme Canonical Knowledge Base,
maintaining persistent multi-turn conversational context, anaphora resolution, and citizen profile awareness.
"""

import re
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from services.db import get_user_language
from services.i18n import get_text, DEFAULT_LANGUAGE
from services.privacy import PrivacyGuard
from services.readiness import ApplicationReadinessTracker
from services.groq_service import GroqService
from database.repository import (
    SchemeRepository,
    CitizenProfileRepository,
    ConversationContextRepository,
    CitizenSavedSchemeRepository,
)
from database.models import CitizenProfile
from rag.document_processor import DocumentProcessor
from rag.embeddings import LocalEmbeddingEngine
from rag.vector_store import LocalVectorStore
from rag.retriever import HybridRetriever
from rag.answer_generator import AnswerGenerator
from chatbot.profile_extractor import ProfileExtractor

router = Router(name="help_router")


def get_scheme_quick_actions(scheme_id: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Builds interactive follow-up pill buttons for the active scheme."""
    txt_apply = "📝 " + ("आवेदन कैसे करें" if lang == "hi" else ("अर्ज कसा करावा" if lang == "mr" else "How to Apply"))
    txt_docs = "📄 " + ("दस्तावेज" if lang == "hi" else ("कागदपत्रे" if lang == "mr" else "Documents"))
    txt_amt = "💰 " + ("लाभ राशि" if lang == "hi" else ("लाभाची रक्कम" if lang == "mr" else "Benefit Amount"))
    txt_ready = "📋 " + ("तैयारी" if lang == "hi" else ("तयारी" if lang == "mr" else "Readiness"))
    txt_save = "📌 " + ("सहेजें" if lang == "hi" else ("जतन करा" if lang == "mr" else "Save"))

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=txt_apply, callback_data=f"act_apply:{scheme_id}"),
                InlineKeyboardButton(text=txt_docs, callback_data=f"act_docs:{scheme_id}"),
            ],
            [
                InlineKeyboardButton(text=txt_amt, callback_data=f"act_amt:{scheme_id}"),
                InlineKeyboardButton(text=txt_ready, callback_data=f"act_ready:{scheme_id}"),
            ],
            [
                InlineKeyboardButton(text=txt_save, callback_data=f"act_save:{scheme_id}"),
            ],
        ]
    )


# Lazy-loaded singleton RAG engine for the Telegram bot
logger = logging.getLogger(__name__)
_retriever = None
_generator = None
_groq_service = GroqService()


def get_telegram_rag():
    global _retriever, _generator
    if _retriever is None or _generator is None:
        repo = SchemeRepository()
        schemes = repo.list_all_schemes()
        processor = DocumentProcessor()
        chunks = []
        for s in schemes:
            chunks.extend(processor.process_scheme_record(s))

        engine = LocalEmbeddingEngine()
        store = LocalVectorStore(engine)
        store.add_chunks(chunks)

        _retriever = HybridRetriever(store)
        _generator = AnswerGenerator()
    return _retriever, _generator


def is_followup_query(query: str) -> bool:
    """Detects whether a query is a conversational follow-up without explicitly naming a scheme."""
    q = query.lower().strip()
    followup_patterns = [
        r"\b(how to apply|how do i apply|how can i apply|application process|where to apply|process|apply)\b",
        r"\b(what documents|documents required|which documents|papers required|documents needed|documents)\b",
        r"\b(am i eligible|can i apply|am i qualify|who can apply|eligibility|age limit|income limit)\b",
        r"\b(how much|how much money|benefits|benefit|amount|pension amount|subsidy)\b",
        r"\b(what is the link|website|portal|link|official site)\b",
        r"\b(for this|about this|for it|about it|in this scheme|this one|first one|second one|it)\b",
        r"\b(आवेदन कैसे|दस्तावेज क्या|पात्रता क्या|लाभ क्या|वेबसाइट|पोर्टल|इसके लिए|इसमें|पात्र हूँ)\b",
        r"\b(अर्ज कसा|कागदपत्रे काय|पात्रता काय|फायदे काय|संकेतस्थळ|यासाठी|यात|पात्र आहे)\b",
    ]
    return any(re.search(pat, q) for pat in followup_patterns)


@router.message(Command("help"))
async def handle_help_command(message: Message) -> None:
    """Handles the /help command in the user's preferred language."""
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    help_message = get_text("help_text", lang)
    await message.answer(
        text=help_message,
        parse_mode="Markdown",
    )


async def process_citizen_query_text(message: Message, raw_text: str, lang: str) -> None:
    """Core RAG & Scheme Intelligence execution pipeline with Groq LLM + local fallback."""
    user_id = str(message.from_user.id)

    # Privacy Protection Guard: Intercept and mask sensitive credentials
    privacy_check = PrivacyGuard.check_sensitive_content(raw_text, language=lang)
    if privacy_check["has_sensitive_data"]:
        await message.answer(text=privacy_check["warning"], parse_mode="Markdown")
        user_text = privacy_check["sanitized_text"]
    else:
        user_text = raw_text

    profile_repo = CitizenProfileRepository()
    ctx_repo = ConversationContextRepository()
    saved_repo = CitizenSavedSchemeRepository()

    current_profile = profile_repo.get_profile(user_id) or CitizenProfile(user_id=user_id, language=lang)
    context = ctx_repo.get_context(user_id)

    # 1. Check for reset or clear context command
    if user_text.strip().lower() in ("reset", "delete profile", "restart", "start over", "माहिती हटवा", "मिटाएं", "clear"):
        saved_repo.clear_user_data(user_id)
        if lang == "hi":
            reply = "🗑️ आपकी प्रोफाइल एवं चैट संदर्भ हटा दिया गया है। आप /start भेजकर नए सिरे से शुरुआत कर सकते हैं।"
        elif lang == "mr":
            reply = "🗑️ आपली प्रोफाइल आणि चॅट संदर्भ हटवण्यात आला आहे. आपण /start पाठवून नव्याने सुरुवात करू शकता."
        else:
            reply = "🗑️ Your profile data and conversation history have been cleared. Send /start to begin fresh anytime."
        await message.answer(text=reply)
        return

    # 2. Extract profile attributes if mentioned in message
    updated_profile = ProfileExtractor.extract_from_text(user_text, current_profile)
    profile_repo.save_profile(updated_profile)

    # 3. Contextual Query Rewriting
    active_scheme_name = context.get("active_scheme_name")
    if is_followup_query(user_text) and active_scheme_name:
        search_query = f"{user_text} {active_scheme_name}"
    else:
        search_query = user_text

    # 4. Retrieve matching scheme records via Local RAG
    retriever, generator = get_telegram_rag()
    retrieved = retriever.retrieve(query=search_query, top_k=3, state_filter=updated_profile.state)

    # If a scheme was found, update the active scheme in context memory and record view history
    top_scheme_id = None
    if retrieved and retrieved[0].get("metadata", {}).get("scheme_id"):
        top_meta = retrieved[0]["metadata"]
        top_scheme_id = top_meta["scheme_id"]
        ctx_repo.set_active_scheme(user_id, top_meta["scheme_id"], top_meta["scheme_name"])
        saved_repo.record_view_history(user_id, top_scheme_id)

    # 5. Synthesize answer: try Groq LLM first, fallback to local generator
    rag_response = None
    if _groq_service.is_configured:
        try:
            rag_response = await _groq_service.synthesize_scheme_answer(
                query=user_text,
                retrieved_passages=retrieved,
                language=lang,
                profile=updated_profile,
                context=context,
            )
        except Exception as e:
            logger.warning(f"Groq LLM synthesis encountered error, falling back to local engine: {e}")

    if not rag_response:
        rag_response = generator.generate_answer(
            query=user_text,
            retrieved_passages=retrieved,
            language=lang,
            profile=updated_profile,
            context=context,
        )

    answer_text = rag_response.get("answer", "")
    citations = rag_response.get("citations", [])

    # Format citations
    if citations:
        if lang == "hi":
            cit_header = "\n\n📌 *सत्यापित सरकारी स्रोत:*"
        elif lang == "mr":
            cit_header = "\n\n📌 *अधिकृत शासकीय संदर्भ:*"
        else:
            cit_header = "\n\n📌 *Verified Government Sources:*"

        cit_lines = [f"• **{c['scheme_name']}** — [Official Link]({c['source_url']})" for c in citations[:2]]
        answer_text += cit_header + "\n" + "\n".join(cit_lines)

    # 6. Save conversational turns
    ctx_repo.add_turn(user_id, "user", user_text, top_scheme_id)
    ctx_repo.add_turn(user_id, "assistant", answer_text, top_scheme_id)

    # 7. Send message with markdown parsing and resilient fallback
    kb = get_scheme_quick_actions(top_scheme_id, lang) if top_scheme_id else None
    try:
        await message.answer(text=answer_text, reply_markup=kb, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception:
        await message.answer(text=answer_text, reply_markup=kb, disable_web_page_preview=True)


@router.message(F.voice)
@router.message(F.audio)
async def handle_citizen_voice(message: Message) -> None:
    """
    Multilingual Voice Assistant Handler:
    Transcribes audio notes using Groq Whisper (whisper-large-v3) and answers using Scheme Intelligence.
    """
    voice_obj = message.voice or message.audio
    if not voice_obj:
        return

    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE

    if not _groq_service.is_configured:
        err_msg = (
            "🎙️ *Voice Assistant Notice:*\nVoice message received! Audio transcription requires a configured Groq key. Please type your question in the chat."
            if lang == "en" else
            "🎙️ *ध्वनि संदेश सूचना:*\nध्वनि संदेश प्राप्त हुआ! ऑडियो ट्रांसक्रिप्शन सेवा अनुपलब्ध होने पर कृपया अपना प्रश्न लिखकर भेजें।"
        )
        await message.answer(text=err_msg, parse_mode="Markdown")
        return

    try:
        file_info = await message.bot.get_file(voice_obj.file_id)
        file_stream = await message.bot.download_file(file_info.file_path)
        audio_bytes = file_stream.read()

        # Transcribe with Whisper
        transcription = await _groq_service.transcribe_audio(audio_bytes, filename="voice.ogg")
        if not transcription or not transcription.strip():
            no_speech = (
                "🎙️ *Could not clearly transcribe speech.* Please speak clearly closer to your microphone, or type your query below."
                if lang == "en" else
                "🎙️ *आवाज़ स्पष्ट रूप से सुनाई नहीं दी।* कृपया माइक्रोफ़ोन के पास आकर पुनः बोलें या अपना प्रश्न लिखकर भेजें।"
            )
            await message.answer(text=no_speech, parse_mode="Markdown")
            return

        # Echo recognized speech
        heard_prefix = "🎙️ **I heard:** " if lang == "en" else ("🎙️ **सुनाई दिया:** " if lang == "hi" else "🎙️ **ऐकले:** ")
        await message.answer(text=f"{heard_prefix}*\"{transcription}\"*", parse_mode="Markdown")

        # Route query through scheme intelligence
        await process_citizen_query_text(message, transcription, lang)
    except Exception as e:
        logger.error(f"Voice handler exception: {e}", exc_info=True)
        await message.answer(text="⚠️ *Could not process voice note right now.* Please type your query in chat.", parse_mode="Markdown")


@router.message()
async def handle_citizen_query(message: Message) -> None:
    """
    Text Query Handler:
    Maintains active scheme context, resolves follow-up questions, personalizes responses,
    and enforces strict privacy safeguards against credential collection.
    """
    raw_text = message.text or ""
    if not raw_text.strip():
        return

    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    await process_citizen_query_text(message, raw_text, lang)


# ---------------- Interactive Scheme Quick Action Callbacks ----------------

@router.callback_query(F.data.startswith("act_apply:"))
async def handle_action_apply(callback: CallbackQuery) -> None:
    await callback.answer()
    scheme_id = callback.data.split(":")[1]
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    repo = SchemeRepository()
    scheme = repo.get_scheme_by_id(scheme_id)
    if not scheme:
        return
    retriever, generator = get_telegram_rag()
    passages = [{"text": scheme.description, "metadata": {"scheme_id": scheme.scheme_id, "scheme_name": scheme.scheme_name, "section": "Application & Documents"}}]
    ans = generator.generate_answer(f"How do I apply for {scheme.scheme_name}?", passages=passages, language=lang)
    if callback.message:
        await callback.message.answer(text=ans["answer"], reply_markup=get_scheme_quick_actions(scheme_id, lang), parse_mode="Markdown", disable_web_page_preview=True)


@router.callback_query(F.data.startswith("act_docs:"))
async def handle_action_docs(callback: CallbackQuery) -> None:
    await callback.answer()
    scheme_id = callback.data.split(":")[1]
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    repo = SchemeRepository()
    scheme = repo.get_scheme_by_id(scheme_id)
    if not scheme:
        return
    retriever, generator = get_telegram_rag()
    passages = [{"text": scheme.description, "metadata": {"scheme_id": scheme.scheme_id, "scheme_name": scheme.scheme_name, "section": "Application & Documents"}}]
    ans = generator.generate_answer(f"What documents are required for {scheme.scheme_name}?", passages=passages, language=lang)
    if callback.message:
        await callback.message.answer(text=ans["answer"], reply_markup=get_scheme_quick_actions(scheme_id, lang), parse_mode="Markdown", disable_web_page_preview=True)


@router.callback_query(F.data.startswith("act_amt:"))
async def handle_action_amount(callback: CallbackQuery) -> None:
    await callback.answer()
    scheme_id = callback.data.split(":")[1]
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    repo = SchemeRepository()
    scheme = repo.get_scheme_by_id(scheme_id)
    if not scheme:
        return
    retriever, generator = get_telegram_rag()
    passages = [{"text": scheme.description, "metadata": {"scheme_id": scheme.scheme_id, "scheme_name": scheme.scheme_name, "section": "Overview & Benefits"}}]
    ans = generator.generate_answer(f"How much money do I get under {scheme.scheme_name}?", passages=passages, language=lang)
    if callback.message:
        await callback.message.answer(text=ans["answer"], reply_markup=get_scheme_quick_actions(scheme_id, lang), parse_mode="Markdown", disable_web_page_preview=True)


@router.callback_query(F.data.startswith("act_ready:"))
async def handle_action_readiness(callback: CallbackQuery) -> None:
    await callback.answer()
    scheme_id = callback.data.split(":")[1]
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    repo = SchemeRepository()
    scheme = repo.get_scheme_by_id(scheme_id)
    if not scheme:
        return
    tracker = ApplicationReadinessTracker()
    rep = tracker.evaluate_readiness(scheme, user_id=str(callback.from_user.id), language=lang)
    text = tracker.format_readiness_telegram(rep, language=lang)
    if callback.message:
        await callback.message.answer(text=text, parse_mode="Markdown")


@router.callback_query(F.data.startswith("act_save:"))
async def handle_action_save(callback: CallbackQuery) -> None:
    scheme_id = callback.data.split(":")[1]
    user_id = str(callback.from_user.id)
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    repo = SchemeRepository()
    saved_repo = CitizenSavedSchemeRepository()
    scheme = repo.get_scheme_by_id(scheme_id)
    if scheme:
        saved_repo.save_scheme(user_id, scheme_id)
        alert_msg = f"📌 {scheme.scheme_name} saved to your dashboard!" if lang == "en" else f"📌 {scheme.scheme_name} आपकी प्रोफाइल में सहेज ली गई है!"
        await callback.answer(text=alert_msg, show_alert=True)
    else:
        await callback.answer()
