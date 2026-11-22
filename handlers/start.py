"""
Start command handler and main menu callbacks for Civicsaathi Telegram Bot.
Powered by the Canonical Scheme Knowledge Base & Deterministic Eligibility Engine.
"""

import re
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
)

from services.db import get_user_language
from services.i18n import (
    INITIAL_LANGUAGE_PROMPT,
    LANGUAGE_CHANGE_PROMPT,
    get_text,
    DEFAULT_LANGUAGE,
)
from database.repository import (
    SchemeRepository,
    CitizenProfileRepository,
    CitizenSavedSchemeRepository,
    ConversationContextRepository,
)
from services.recommendation import RecommendationService
from services.dashboard import CitizenDashboardService
from services.comparison import SchemeComparisonService
from services.readiness import ApplicationReadinessTracker
from services.admin import AdminVerificationService
from handlers.language import get_language_keyboard
from handlers.interview import start_interview_flow, router as interview_router

router = Router(name="start_router")
router.include_router(interview_router)

# Callback identifiers
CB_START_INTERVIEW = "menu_interview"
CB_SCHEMES = "menu_schemes"
CB_PROFILE = "menu_profile"
CB_RECOMMENDED = "menu_recommended"
CB_DOCUMENTS = "menu_documents"
CB_HELPLINE = "menu_helpline"
CB_LANGUAGE = "menu_language"
CB_HELP = "menu_help"
CB_COMPARE = "menu_compare"
CB_READINESS = "menu_readiness"


def get_main_menu_keyboard(lang: str = DEFAULT_LANGUAGE, include_advanced: bool = False) -> InlineKeyboardMarkup:
    """Builds the 7-button main menu keyboard (or extended 9-button when include_advanced=True)."""
    buttons = [
        [
            InlineKeyboardButton(
                text=get_text("btn_schemes", lang),
                callback_data=CB_SCHEMES,
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("btn_profile", lang),
                callback_data=CB_PROFILE,
            ),
            InlineKeyboardButton(
                text=get_text("btn_recommended", lang),
                callback_data=CB_RECOMMENDED,
            ),
        ],
    ]

    if include_advanced:
        buttons.append([
            InlineKeyboardButton(
                text="⚖️ " + ("योजना तुलना" if lang == "hi" else ("योजना तुलना" if lang == "mr" else "Compare Schemes")),
                callback_data=CB_COMPARE,
            ),
            InlineKeyboardButton(
                text="📋 " + ("तैयारी ट्रैकर" if lang == "hi" else ("तयारी ट्रॅकर" if lang == "mr" else "Readiness Tracker")),
                callback_data=CB_READINESS,
            ),
        ])

    buttons.extend([
        [
            InlineKeyboardButton(
                text=get_text("btn_documents", lang),
                callback_data=CB_DOCUMENTS,
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("btn_helpline", lang),
                callback_data=CB_HELPLINE,
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("btn_language", lang),
                callback_data=CB_LANGUAGE,
            ),
            InlineKeyboardButton(
                text=get_text("btn_help", lang),
                callback_data=CB_HELP,
            ),
        ],
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext) -> None:
    """Handles /start command: triggers language selection or launches guided onboarding."""
    user_id = message.from_user.id
    saved_lang = get_user_language(user_id)

    if not saved_lang:
        await message.answer(
            text=INITIAL_LANGUAGE_PROMPT,
            reply_markup=get_language_keyboard(),
        )
    else:
        profile_repo = CitizenProfileRepository()
        profile = profile_repo.get_profile(str(user_id))
        has_profile = profile is not None and (profile.age is not None or profile.occupation is not None)

        if not has_profile:
            # First time user with language set: launch Step 1 (Name) immediately
            welcome_text = get_text("welcome_back", saved_lang)
            await message.answer(text=welcome_text, parse_mode="Markdown")
            await start_interview_flow(message, state, saved_lang)
        else:
            # Returning user with completed profile: greet warmly by name
            name_display = profile.full_name or ("नागरिक" if saved_lang != "en" else "Citizen")
            if saved_lang == "hi":
                welcome_text = (
                    f"🙏 **नमस्ते {name_display} जी! नागरिक साथी में आपका पुनः स्वागत है 🇮🇳**\n\n"
                    f"📋 **आपकी सक्रिय प्रोफाइल:**\n"
                    f"• **राज्य:** {profile.state or 'समस्त भारत'} | **व्यवसाय:** {profile.occupation or 'व्यवसाय'}\n"
                    f"• **आयु:** {profile.age or '30'} वर्ष | **वर्ग:** {profile.category or 'General'}\n\n"
                    f"आप अपनी योजनाएं देख सकते हैं, प्रोफाइल अपडेट कर सकते हैं, या सीधे चैट में कोई भी सवाल पूछ सकते हैं!"
                )
            elif saved_lang == "mr":
                welcome_text = (
                    f"🙏 **नमस्कार {name_display}! नागरीक साथी मध्ये आपले पुन्हा स्वागत आहे 🇮🇳**\n\n"
                    f"📋 **आपली सक्रिय प्रोफाइल:**\n"
                    f"• **राज्य:** {profile.state or 'संपूर्ण भारत'} | **व्यवसाय:** {profile.occupation or 'व्यवसाय'}\n"
                    f"• **वय:** {profile.age or '30'} वर्षे | **प्रवर्ग:** {profile.category or 'General'}\n\n"
                    f"आपण आपल्या योजना पाहू शकता, प्रोफाइल अपडेट करू शकता किंवा थेट चॅटमध्ये कोणताही प्रश्न विचारू शकता!"
                )
            else:
                welcome_text = (
                    f"🙏 **Namaste {name_display}! Welcome back to Civicsaathi 🇮🇳**\n\n"
                    f"📋 **Your Active Profile:**\n"
                    f"• **State:** {profile.state or 'Pan-India'} | **Occupation:** {profile.occupation or 'N/A'}\n"
                    f"• **Age:** {profile.age or 'N/A'} yrs | **Category:** {profile.category or 'General'}\n\n"
                    f"Discover tailored schemes below, update your profile, or ask any question directly in chat!"
                )
            await message.answer(
                text=welcome_text,
                reply_markup=get_main_menu_keyboard(saved_lang),
                parse_mode="Markdown",
            )


@router.message(Command("interview"))
@router.message(Command("check"))
async def handle_interview_command(message: Message, state: FSMContext) -> None:
    """Direct command to start the step-by-step interview."""
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    await start_interview_flow(message, state, lang)


@router.callback_query(F.data == CB_START_INTERVIEW)
async def handle_start_interview_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Handles 1-click start interview button."""
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await callback.answer()
    if callback.message:
        await start_interview_flow(callback.message, state, lang)


@router.callback_query(F.data == CB_SCHEMES)
async def handle_schemes_button(callback: CallbackQuery) -> None:
    """Displays top schemes from the verified knowledge base."""
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await callback.answer()

    if lang == "hi":
        text = (
            "🏛️ *प्रमुख सरकारी योजनाएँ (Central Schemes):*\n\n"
            "🌾 *कृषि एवं किसान:*\n"
            "• **PM-KISAN:** ₹6,000 प्रति वर्ष 3 किश्तों में\n"
            "• **किसान क्रेडिट कार्ड (KCC):** 7% रियायती अल्पावधि ऋण\n"
            "• **फसल बीमा (PMFBY):** नाममात्र प्रीमियम पर सुरक्षा\n\n"
            "🛡️ *बीमा एवं सामाजिक सुरक्षा:*\n"
            "• **PMJJBY:** ₹2 लाख जीवन बीमा (मात्र ₹436/वर्ष)\n"
            "• **PMSBY:** ₹2 लाख दुर्घटना बीमा (मात्र ₹20/वर्ष)\n"
            "• **अटल पेंशन योजना (APY):** 60 वर्ष के बाद गारंटीड मासिक पेंशन\n\n"
            "👩 *महिला एवं परिवार कल्याण:*\n"
            "• **PMMVY 2.0:** ₹5,000 / ₹6,000 मातृत्व सहायता\n"
            "• **सुकन्या समृद्धि योजना:** 8.2% कर-मुक्त ब्याज दर\n\n"
            "💼 *ऋण एवं स्वरोजगार:*\n"
            "• **मुद्रा लोन (PMMY):** ₹20 लाख तक का व्यवसाय ऋण\n"
            "• **PM विश्वकर्मा:** ₹15,000 टूलकिट व रियायती ऋण\n\n"
            "💬 *किसी भी योजना की जानकारी के लिए उसका नाम लिखकर भेजें!*"
        )
    elif lang == "mr":
        text = (
            "🏛️ *प्रमुख शासकीय योजना (Central Schemes):*\n\n"
            "🌾 *शेती आणि शेतकरी:*\n"
            "• **PM-KISAN:** वर्षाला ₹6,000 थेट बँक खात्यात\n"
            "• **किसान क्रेडिट कार्ड (KCC):** 7% सवलतीच्या दरात पीक कर्ज\n"
            "• **पंतप्रधान पीक विमा (PMFBY):** कमी प्रीमियमवर विमा संरक्षण\n\n"
            "🛡️ *विमा आणि सामाजिक सुरक्षा:*\n"
            "• **PMJJBY:** ₹2 लाख जीवन विमा (फक्त ₹436/वर्ष)\n"
            "• **PMSBY:** ₹2 लाख अपघात विमा (फक्त ₹20/वर्ष)\n"
            "• **अटल पेन्शन योजना (APY):** वयाच्या 60 नंतर हमी पेन्शन\n\n"
            "👩 *महिला आणि कुटुंब कल्याण:*\n"
            "• **PMMVY 2.0:** ₹5,000 / ₹6,000 मातृत्व सहाय्य\n"
            "• **सुकन्या समृद्धी योजना:** 8.2% करमुक्त व्याज\n\n"
            "💼 *कर्ज आणि स्वयंरोजगार:*\n"
            "• **मुद्रा योजना (PMMY):** ₹20 लाखांपर्यंत व्यवसाय कर्ज\n"
            "• **PM विश्वकर्मा:** ₹15,000 टूलकिट आणि सवलतीचे कर्ज\n\n"
            "💬 *कोणत्याही योजनेची माहिती हवी असल्यास थेट नाव लिहून पाठवा!*"
        )
    else:
        text = (
            "🏛️ *Verified Government Schemes (Batch 1 Central):*\n\n"
            "🌾 *Agriculture & Farmers:*\n"
            "• **PM-KISAN:** ₹6,000/year income support in 3 instalments\n"
            "• **Kisan Credit Card (KCC):** 7% concessional short-term crop loans\n"
            "• **PMFBY:** Subsidized seasonal crop insurance\n\n"
            "🛡️ *Insurance & Social Security:*\n"
            "• **PMJJBY:** ₹2,00,000 life insurance for ₹436/year\n"
            "• **PMSBY:** ₹2,00,000 accident cover for ₹20/year\n"
            "• **Atal Pension Yojana (APY):** Guaranteed monthly pension at age 60\n\n"
            "👩 *Women & Family Welfare:*\n"
            "• **PMMVY 2.0:** ₹5,000 / ₹6,000 maternity cash incentive\n"
            "• **Sukanya Samriddhi (SSY):** 8.2% tax-free interest small savings\n\n"
            "💼 *Enterprise & Loans:*\n"
            "• **Mudra Loan (PMMY):** Up to ₹20,00,000 across 4 tiers\n"
            "• **PM Vishwakarma:** ₹15,000 toolkit + collateral-free loans\n\n"
            "💬 *Tip: Type any question or scheme name in chat to get instant details!*"
        )

    btn_start_txt = {
        "hi": "🚀 1-मिनट पात्रता जाँच शुरू करें",
        "mr": "🚀 १-मिनिटात पात्रता तपासणी सुरू करा",
        "en": "🚀 Start 1-Min Eligibility Assessment",
    }.get(lang, "🚀 Start 1-Min Assessment")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=btn_start_txt, callback_data=CB_START_INTERVIEW)]]
    )

    if callback.message:
        await callback.message.answer(text=text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == CB_RECOMMENDED)
async def handle_recommended_button(callback: CallbackQuery) -> None:
    """Calculates and displays recommended schemes for the user."""
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await callback.answer()

    profile_repo = CitizenProfileRepository()
    profile = profile_repo.get_profile(str(callback.from_user.id))

    if not profile or (not profile.age and not profile.occupation and not profile.state):
        if lang == "hi":
            prompt = (
                "⭐ *अनुशंसित योजनाएँ (Recommended Schemes)*\n\n"
                "आपके लिए सटीक योजनाएँ खोजने के लिए केवल 1 मिनट की पात्रता जाँच पूरी करें।"
            )
            btn_txt = "🚀 1-मिनट पात्रता जाँच शुरू करें"
        elif lang == "mr":
            prompt = (
                "⭐ *माझ्यासाठी शिफारस केलेल्या योजना*\n\n"
                "आपल्यासाठी योग्य योजना शोधण्यासाठी फक्त १ मिनिटांची पात्रता तपासणी पूर्ण करा."
            )
            btn_txt = "🚀 १-मिनिटात तपासणी सुरू करा"
        else:
            prompt = (
                "⭐ *Personalised Scheme Recommendations*\n\n"
                "To recommend schemes tailored for you, take a quick 1-minute assessment!"
            )
            btn_txt = "🚀 Start 1-Min Eligibility Check"

        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=btn_txt, callback_data=CB_START_INTERVIEW)]]
        )
        if callback.message:
            await callback.message.answer(text=prompt, reply_markup=kb, parse_mode="Markdown")
        return

    repo = SchemeRepository()
    rec_service = RecommendationService(repo)
    recs = rec_service.get_recommendations_for_profile(profile)

    if lang == "hi":
        heading = f"⭐ *आपकी प्रोफाइल के अनुसार शीर्ष योजनाएँ ({len(recs)} मिलीं):*\n\n"
    elif lang == "mr":
        heading = f"⭐ *आपल्या प्रोफाइलनुसार योग्य योजना ({len(recs)} आढळल्या):*\n\n"
    else:
        heading = f"⭐ *Recommended Schemes for You ({len(recs)} found):*\n\n"

    items = []
    for r in recs[:5]:
        badge = "✅ पात्र (Eligible)" if r.overall_status == "ELIGIBLE" else "⚠️ सत्यापन आवश्यक (Needs Verification)"
        items.append(f"• **{r.scheme_name}**\n  स्थिति: {badge}\n  लाभ: {r.benefit_summary}\n")

    full_text = heading + "\n".join(items)
    txt_compare = "⚖️ " + ("योजना तुलना" if lang == "hi" else ("योजना तुलना" if lang == "mr" else "Compare Top Schemes"))
    txt_ready = "📋 " + ("तैयारी जांचें" if lang == "hi" else ("तयारी तपासा" if lang == "mr" else "Check Readiness"))
    rec_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=txt_compare, callback_data=CB_COMPARE),
                InlineKeyboardButton(text=txt_ready, callback_data=CB_READINESS),
            ]
        ]
    )
    if callback.message:
        await callback.message.answer(text=full_text, reply_markup=rec_kb, parse_mode="Markdown")


@router.callback_query(F.data == CB_PROFILE)
async def handle_profile_button(callback: CallbackQuery) -> None:
    """Shows comprehensive citizen dashboard."""
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await callback.answer()

    dashboard_service = CitizenDashboardService()
    data = dashboard_service.get_dashboard_data(str(callback.from_user.id), language=lang)
    text = dashboard_service.format_dashboard_telegram(data, language=lang)

    btn_txt = {
        "hi": "🔄 1-मिनट प्रोफाइल अपडेट करें",
        "mr": "🔄 १-मिनिटात प्रोफाईल अपडेट करा",
        "en": "🔄 Take / Update 1-Min Assessment",
    }.get(lang, "🔄 Take / Update Assessment")

    update_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=btn_txt, callback_data=CB_START_INTERVIEW)]]
    )
    if callback.message:
        await callback.message.answer(text=text, reply_markup=update_kb, parse_mode="Markdown")


@router.callback_query(F.data == CB_COMPARE)
async def handle_compare_button(callback: CallbackQuery) -> None:
    """Handles comparison button click."""
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await callback.answer()

    profile = CitizenProfileRepository().get_profile(str(callback.from_user.id))
    targets = []
    if profile:
        recs = RecommendationService(SchemeRepository()).get_recommendations_for_profile(profile)
        targets = [r.scheme_name for r in recs[:3]]
    if len(targets) < 2:
        targets = ["PM-KISAN", "KCC", "PMSBY"]

    comparator = SchemeComparisonService()
    report = comparator.compare_schemes(targets, language=lang)
    text = comparator.format_comparison_telegram(report, language=lang)
    if callback.message:
        await callback.message.answer(text=text, parse_mode="Markdown", disable_web_page_preview=True)


@router.callback_query(F.data == CB_READINESS)
async def handle_readiness_button(callback: CallbackQuery) -> None:
    """Handles readiness tracker button click."""
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await callback.answer()

    repo = SchemeRepository()
    ctx = ConversationContextRepository().get_context(str(callback.from_user.id))
    scheme_id = ctx.get("active_scheme_id")
    if not scheme_id:
        profile = CitizenProfileRepository().get_profile(str(callback.from_user.id))
        if profile:
            recs = RecommendationService(repo).get_recommendations_for_profile(profile)
            if recs:
                scheme_id = recs[0].scheme_id
    if not scheme_id:
        scheme_id = "GOI-CEN-004"
    scheme = repo.get_scheme_by_id(scheme_id) or repo.list_all_schemes()[0]

    tracker = ApplicationReadinessTracker()
    rep = tracker.evaluate_readiness(scheme, user_id=str(callback.from_user.id), language=lang)
    text = tracker.format_readiness_telegram(rep, language=lang)
    if callback.message:
        await callback.message.answer(text=text, parse_mode="Markdown")


@router.message(Command("dashboard"))
@router.message(Command("profile"))
async def handle_dashboard_command(message: Message) -> None:
    """Direct command to open citizen dashboard."""
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    dashboard_service = CitizenDashboardService()
    data = dashboard_service.get_dashboard_data(str(message.from_user.id), language=lang)
    text = dashboard_service.format_dashboard_telegram(data, language=lang)
    await message.answer(text=text, parse_mode="Markdown")


@router.message(Command("compare"))
async def handle_compare_command(message: Message) -> None:
    """Direct command to compare schemes, e.g. /compare KCC vs PM-KISAN."""
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    args = (message.text or "").replace("/compare", "").strip()
    comparator = SchemeComparisonService()
    if args:
        parts = [p.strip() for p in re.split(r"\bvs\b|,|\s+", args, flags=re.IGNORECASE) if p.strip()]
        report = comparator.compare_schemes(parts, language=lang)
    else:
        report = comparator.compare_schemes(["PM-KISAN", "KCC"], language=lang)
    text = comparator.format_comparison_telegram(report, language=lang)
    await message.answer(text=text, parse_mode="Markdown", disable_web_page_preview=True)


@router.message(Command("readiness"))
async def handle_readiness_command(message: Message) -> None:
    """Direct command to evaluate application readiness for a scheme."""
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    args = (message.text or "").replace("/readiness", "").strip()
    repo = SchemeRepository()
    scheme = None
    if args:
        scheme = repo.get_scheme_by_id(args)
        if not scheme:
            for s in repo.list_all_schemes():
                if args.lower() in s.scheme_name.lower() or any(args.lower() in a.lower() for a in s.alternate_names):
                    scheme = s
                    break
    if not scheme:
        ctx = ConversationContextRepository().get_context(str(message.from_user.id))
        if ctx.get("active_scheme_id"):
            scheme = repo.get_scheme_by_id(ctx["active_scheme_id"])
    if not scheme:
        scheme = repo.get_scheme_by_id("GOI-CEN-004") or repo.list_all_schemes()[0]

    tracker = ApplicationReadinessTracker()
    rep = tracker.evaluate_readiness(scheme, user_id=str(message.from_user.id), language=lang)
    text = tracker.format_readiness_telegram(rep, language=lang)
    await message.answer(text=text, parse_mode="Markdown")


@router.message(Command("admin"))
async def handle_admin_command(message: Message) -> None:
    """Administrative verification dashboard."""
    admin_service = AdminVerificationService()
    text = admin_service.format_admin_summary_telegram()
    await message.answer(text=text, parse_mode="Markdown")


@router.message(Command("save"))
async def handle_save_command(message: Message) -> None:
    """Saves / bookmarks a scheme to citizen profile."""
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    args = (message.text or "").replace("/save", "").strip()
    user_id = str(message.from_user.id)
    repo = SchemeRepository()
    saved_repo = CitizenSavedSchemeRepository()
    target_id = args
    if not target_id:
        ctx = ConversationContextRepository().get_context(user_id)
        target_id = ctx.get("active_scheme_id")
    scheme = repo.get_scheme_by_id(target_id) if target_id else None
    if scheme:
        saved_repo.save_scheme(user_id, scheme.scheme_id)
        msg = f"📌 **{scheme.scheme_name}** has been saved to your dashboard!" if lang == "en" else f"📌 **{scheme.scheme_name}** आपकी प्रोफाइल में सहेज ली गई है!"
    else:
        msg = "❌ Please specify a scheme to save, e.g. `/save GOI-CEN-004`" if lang == "en" else "❌ कृपया सहेजने के लिए योजना बताएं (उदा. `/save GOI-CEN-004`)"
    await message.answer(text=msg, parse_mode="Markdown")


@router.message(Command("reset"))
async def handle_reset_command(message: Message) -> None:
    """Permanently deletes citizen profile and history (DPDP Act compliance)."""
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    user_id = str(message.from_user.id)
    CitizenSavedSchemeRepository().clear_user_data(user_id)
    if lang == "hi":
        reply = "🗑️ आपकी सभी प्रोफाइल जानकारी, सहेजी गई योजनाएं और चैट संदर्भ हमेशा के लिए मिटा दिए गए हैं।"
    elif lang == "mr":
        reply = "🗑️ आपली सर्व माहिती, जतन केलेल्या योजना आणि चॅट इतिहास पूर्णपणे हटवण्यात आला आहे."
    else:
        reply = "🗑️ All your personal profile records, saved schemes, and conversation memory have been permanently deleted."
    await message.answer(text=reply, parse_mode="Markdown")


@router.callback_query(F.data == CB_DOCUMENTS)
async def handle_documents_button(callback: CallbackQuery) -> None:
    """Shows verified document checklist."""
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await callback.answer()

    if lang == "hi":
        text = (
            "📄 *सरकारी योजनाओं के लिए आवश्यक दस्तावेज़ चेकलिस्ट:*\n\n"
            "1. 🆔 **पहचान प्रमाण:** आधार कार्ड / मतदाता पहचान पत्र / पैन कार्ड\n"
            "2. 🏦 **बैंक विवरण:** आधार से लिंक बचत बैंक खाता या पोस्ट ऑफिस पासबुक\n"
            "3. 🌾 **भूमि अभिलेख:** खतौनी / 7-12 उतारा / भूमि पट्टे के दस्तावेज़ (किसानों के लिए)\n"
            "4. 📜 **आय प्रमाण:** तहसीलदार या राजस्व विभाग द्वारा जारी आय प्रमाण पत्र\n"
            "5. 🏷️ **जाति / श्रेणी प्रमाण:** SC/ST/OBC/EWS प्रमाण पत्र (यदि लागू हो)\n"
            "6. 🍞 **राशन कार्ड:** BPL या NFSA राशन कार्ड (खाद्य व सामाजिक सुरक्षा योजनाओं हेतु)\n\n"
            "💡 *किसी विशिष्ट योजना के दस्तावेज़ जानने के लिए योजना का नाम लिखकर पूछें!*"
        )
    elif lang == "mr":
        text = (
            "📄 *शासकीय योजनांसाठी आवश्यक कागदपत्रे चेकलिस्ट:*\n\n"
            "१. 🆔 **ओळख पुरावा:** आधार कार्ड / मतदान कार्ड / पॅन कार्ड\n"
            "२. 🏦 **बँक तपशील:** आधार लिंक बँक खाते किंवा पोस्ट ऑफिस पासबुक\n"
            "३. 🌾 **जमीन पुरावा:** ७/१२ उतारा, ८-अ नोंद (शेतकऱ्यांसाठी)\n"
            "४. 📜 **उत्पन्न दाखला:** तहसीलदारांचा अधिकृत उत्पन्नाचा दाखला\n"
            "५. 🏷️ **जात/प्रवर्ग प्रमाणपत्र:** SC/ST/OBC/EWS प्रमाणपत्र (लागू असल्यास)\n"
            "६. 🍞 **रेशन कार्ड:** BPL किंवा अंत्योदय रेशन कार्ड\n\n"
            "💡 *विशिष्ट योजनेची कागदपत्रे जाणून घेण्यासाठी योजनेचे नाव लिहून विचारा!*"
        )
    else:
        text = (
            "📄 *Standard Government Scheme Document Checklist:*\n\n"
            "1. 🆔 **Identity Proof:** Aadhaar Card, Voter ID, or PAN Card\n"
            "2. 🏦 **Bank Account:** Aadhaar-seeded Savings Bank or Post Office passbook\n"
            "3. 🌾 **Land Records:** Revenue-certified landholding papers / 7-12 (for farmers)\n"
            "4. 📜 **Income Certificate:** Issued by competent revenue authority (Tahsildar/SDM)\n"
            "5. 🏷️ **Category Proof:** Valid SC / ST / OBC / EWS certificate (if applicable)\n"
            "6. 🍞 **Ration Card:** BPL / NFSA ration card (for subsidized food & welfare)\n\n"
            "💡 *Ask about any scheme by name in chat to get its exact document list!*"
        )

    btn_start_txt = {
        "hi": "🚀 1-मिनट पात्रता जाँच शुरू करें",
        "mr": "🚀 १-मिनिटात पात्रता तपासणी सुरू करा",
        "en": "🚀 Start 1-Min Eligibility Assessment",
    }.get(lang, "🚀 Start 1-Min Assessment")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=btn_start_txt, callback_data=CB_START_INTERVIEW)]]
    )

    if callback.message:
        await callback.message.answer(text=text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == CB_HELPLINE)
async def handle_helpline_button(callback: CallbackQuery) -> None:
    """Displays genuine, verified Government Helplines."""
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            text=get_text("helpline_response", lang),
            parse_mode="Markdown",
        )


@router.callback_query(F.data == CB_LANGUAGE)
async def handle_language_menu_button(callback: CallbackQuery) -> None:
    """Responds to 'Change Language' button."""
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            text=LANGUAGE_CHANGE_PROMPT,
            reply_markup=get_language_keyboard(),
            parse_mode="Markdown",
        )


@router.callback_query(F.data == CB_HELP)
async def handle_help_menu_button(callback: CallbackQuery) -> None:
    """Responds to 'Help' button."""
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            text=get_text("help_text", lang),
            parse_mode="Markdown",
        )
