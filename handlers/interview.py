"""
Step-by-step interactive citizen profile interview for Civicsaathi Telegram Bot.
Asks each profile question individually and sequentially using aiogram 3 FSM:
1. Name (optional/skippable)
2. State / Union Territory
3. Age
4. Gender
5. Occupation
6. Annual Family Income
7. Social Category

Saves the profile to SQLite, evaluates 30 canonical Central schemes,
presents eligible schemes and documents, and invites follow-up questions.
"""

import logging
import re
from typing import Optional
from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from services.db import get_user_language
from services.i18n import DEFAULT_LANGUAGE
from database.models import CitizenProfile
from database.repository import CitizenProfileRepository, SchemeRepository, ConversationContextRepository
from services.recommendation import RecommendationService

logger = logging.getLogger(__name__)

router = Router(name="interview_router")


class CitizenInterview(StatesGroup):
    waiting_for_name = State()
    waiting_for_state = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_occupation = State()
    waiting_for_income = State()
    waiting_for_category = State()


# ---------------- Keyboards for Each Step ----------------

def get_name_keyboard(lang: str) -> InlineKeyboardMarkup:
    skip_text = {
        "hi": "⏭️ छोड़ें (नाम न बताएं)",
        "mr": "⏭️ वगळा (नाव न सांगता पुढे)",
        "en": "⏭️ Skip (Remain Anonymous)",
    }.get(lang, "⏭️ Skip")
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=skip_text, callback_data="step_skip_name")]]
    )


def get_state_keyboard(lang: str) -> InlineKeyboardMarkup:
    all_india = {"hi": "🇮🇳 संपूर्ण भारत / अन्य", "mr": "🇮🇳 संपूर्ण भारत / इतर", "en": "🇮🇳 Pan-India / Other"}.get(lang, "🇮🇳 Other")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Maharashtra", callback_data="state_Maharashtra"),
                InlineKeyboardButton(text="Uttar Pradesh", callback_data="state_Uttar Pradesh"),
            ],
            [
                InlineKeyboardButton(text="Bihar", callback_data="state_Bihar"),
                InlineKeyboardButton(text="Madhya Pradesh", callback_data="state_Madhya Pradesh"),
            ],
            [
                InlineKeyboardButton(text="Rajasthan", callback_data="state_Rajasthan"),
                InlineKeyboardButton(text="Delhi", callback_data="state_Delhi"),
            ],
            [
                InlineKeyboardButton(text="Karnataka", callback_data="state_Karnataka"),
                InlineKeyboardButton(text="West Bengal", callback_data="state_West Bengal"),
            ],
            [
                InlineKeyboardButton(text=all_india, callback_data="state_all"),
            ],
        ]
    )


def get_age_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="18 – 25 yrs", callback_data="age_21"),
                InlineKeyboardButton(text="26 – 40 yrs", callback_data="age_32"),
            ],
            [
                InlineKeyboardButton(text="41 – 59 yrs", callback_data="age_48"),
                InlineKeyboardButton(text="60+ (Senior)", callback_data="age_62"),
            ],
        ]
    )


def get_gender_keyboard(lang: str) -> InlineKeyboardMarkup:
    male = {"hi": "👨 पुरुष (Male)", "mr": "👨 पुरुष (Male)", "en": "👨 Male"}.get(lang, "👨 Male")
    female = {"hi": "👩 महिला (Female)", "mr": "👩 महिला / स्त्री (Female)", "en": "👩 Female"}.get(lang, "👩 Female")
    other = {"hi": "⚧ अन्य (Other)", "mr": "⚧ इतर (Other)", "en": "⚧ Other"}.get(lang, "⚧ Other")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=male, callback_data="gender_male"),
                InlineKeyboardButton(text=female, callback_data="gender_female"),
            ],
            [
                InlineKeyboardButton(text=other, callback_data="gender_other"),
            ],
        ]
    )


def get_occupation_keyboard(lang: str) -> InlineKeyboardMarkup:
    farmer = {"hi": "🌾 किसान (Farmer)", "mr": "🌾 शेतकरी (Farmer)", "en": "🌾 Farmer"}.get(lang, "🌾 Farmer")
    student = {"hi": "🎓 छात्र (Student)", "mr": "🎓 विद्यार्थी (Student)", "en": "🎓 Student"}.get(lang, "🎓 Student")
    worker = {"hi": "🔨 असंगठित श्रमिक / कामगार", "mr": "🔨 असंघटित कामगार / कारागीर", "en": "🔨 Artisan / Worker"}.get(lang, "🔨 Worker")
    business = {"hi": "💼 स्वरोजगार / व्यापारी", "mr": "💼 व्यावसायिक / स्वयंरोजगार", "en": "💼 Self-Employed"}.get(lang, "💼 Self-Employed")
    homemaker = {"hi": "🏠 गृहिणी (Homemaker)", "mr": "🏠 गृहिणी (Homemaker)", "en": "🏠 Homemaker"}.get(lang, "🏠 Homemaker")
    other = {"hi": "✍️ वेतनभोगी / अन्य", "mr": "✍️ नोकरदार / इतर", "en": "✍️ Salaried / Other"}.get(lang, "✍️ Salaried / Other")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=farmer, callback_data="occ_Farmer"),
                InlineKeyboardButton(text=student, callback_data="occ_Student"),
            ],
            [
                InlineKeyboardButton(text=worker, callback_data="occ_Worker"),
                InlineKeyboardButton(text=business, callback_data="occ_Self-Employed"),
            ],
            [
                InlineKeyboardButton(text=homemaker, callback_data="occ_Homemaker"),
                InlineKeyboardButton(text=other, callback_data="occ_Salaried"),
            ],
        ]
    )


def get_income_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Under ₹1 Lakh", callback_data="inc_80000"),
                InlineKeyboardButton(text="₹1 – 2.5 Lakh", callback_data="inc_180000"),
            ],
            [
                InlineKeyboardButton(text="₹2.5 – 5 Lakh", callback_data="inc_350000"),
                InlineKeyboardButton(text="₹5 – 8 Lakh", callback_data="inc_600000"),
            ],
            [
                InlineKeyboardButton(text="Above ₹8 Lakh", callback_data="inc_900000"),
                InlineKeyboardButton(text="Skip / Unknown", callback_data="inc_200000"),
            ],
        ]
    )


def get_category_keyboard(lang: str) -> InlineKeyboardMarkup:
    gen = {"hi": "सामान्य (General)", "mr": "खुला प्रवर्ग (General)", "en": "General / Open"}.get(lang, "General")
    obc = {"hi": "ओबीसी (OBC)", "mr": "इतर मागासवर्गीय (OBC)", "en": "OBC"}.get(lang, "OBC")
    sc = {"hi": "एससी (SC)", "mr": "अनुसूचित जाती (SC)", "en": "SC"}.get(lang, "SC")
    st = {"hi": "एसटी (ST)", "mr": "अनुसूचित जमाती (ST)", "en": "ST"}.get(lang, "ST")
    minority = {"hi": "अल्पसंख्यक / EWS", "mr": "अल्पसंख्याक / EWS", "en": "EWS / Minority"}.get(lang, "EWS / Minority")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=gen, callback_data="cat_General"),
                InlineKeyboardButton(text=obc, callback_data="cat_OBC"),
            ],
            [
                InlineKeyboardButton(text=sc, callback_data="cat_SC"),
                InlineKeyboardButton(text=st, callback_data="cat_ST"),
            ],
            [
                InlineKeyboardButton(text=minority, callback_data="cat_Minority"),
            ],
        ]
    )


def get_assessment_completion_keyboard(lang: str = DEFAULT_LANGUAGE) -> InlineKeyboardMarkup:
    """Builds interactive action keyboard following assessment completion."""
    txt_compare = "⚖️ " + ("योजना तुलना" if lang == "hi" else ("योजना तुलना" if lang == "mr" else "Compare Top Schemes"))
    txt_ready = "📋 " + ("दस्तावेज़ तैयारी जांचें" if lang == "hi" else ("कागदपत्र तयारी तपासा" if lang == "mr" else "Check Document Readiness"))
    txt_dash = "👤 " + ("मेरा डैशबोर्ड" if lang == "hi" else ("माझे डॅशबोर्ड" if lang == "mr" else "My Dashboard"))
    txt_schemes = "🔍 " + ("सभी योजनाएं" if lang == "hi" else ("सर्व योजना" if lang == "mr" else "Browse Schemes"))

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=txt_compare, callback_data="menu_compare"),
                InlineKeyboardButton(text=txt_ready, callback_data="menu_readiness"),
            ],
            [
                InlineKeyboardButton(text=txt_dash, callback_data="menu_profile"),
                InlineKeyboardButton(text=txt_schemes, callback_data="menu_schemes"),
            ],
        ]
    )


# ---------------- Start Interview Entry Point ----------------

async def start_interview_flow(target_message: Message, state: FSMContext, lang: str) -> None:
    """Initiates the 7-step guided interview."""
    await state.clear()
    await state.set_state(CitizenInterview.waiting_for_name)

    if lang == "hi":
        prompt = (
            "🚀 **नागरिक प्रोफाइल एवं पात्रता जाँच (चरण 1/7):**\n\n"
            "नमस्ते! आपका शुभ नाम क्या है?\n"
            "*(आप अपना नाम टाइप कर सकते हैं, या नाम न बताने के लिए 'छोड़ें' बटन दबाएँ)*"
        )
    elif lang == "mr":
        prompt = (
            "🚀 **नागरिक प्रोफाइल आणि पात्रता तपासणी (पायरी 1/7):**\n\n"
            "नमस्ते! आपले शुभ नाव काय आहे?\n"
            "*(आपण आपले नाव टाईप करू शकता, किंवा नाव न सांगता पुढे जाण्यासाठी 'वगळा' दाबा)*"
        )
    else:
        prompt = (
            "🚀 **Citizen Profile & Eligibility Assessment (Step 1 of 7):**\n\n"
            "Namaste! What is your full name?\n"
            "*(Type your name below, or tap 'Skip' to remain anonymous)*"
        )

    await target_message.answer(
        text=prompt,
        reply_markup=get_name_keyboard(lang),
        parse_mode="Markdown",
    )


# ---------------- Step 1: Name ----------------

@router.callback_query(F.data == "step_skip_name")
async def process_skip_name(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.answer()
    except Exception:
        pass
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    anon_name = "नागरिक (Citizen)" if lang != "en" else "Citizen"
    await state.update_data(full_name=anon_name)
    await ask_state_question(callback.message, state, lang)


@router.message(CitizenInterview.waiting_for_name)
async def process_name_input(message: Message, state: FSMContext) -> None:
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    name_text = (message.text or "").strip()
    if name_text.lower() in ("skip", "छोड़ें", "वगळा", "-"):
        name_text = "नागरिक (Citizen)" if lang != "en" else "Citizen"
    await state.update_data(full_name=name_text)
    await ask_state_question(message, state, lang)


async def ask_state_question(target_message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(CitizenInterview.waiting_for_state)
    if lang == "hi":
        prompt = "📍 **चरण 2/7: आप किस राज्य या केंद्र शासित प्रदेश में रहते हैं?**\n\nनीचे दिए गए राज्यों में से चुनें या अपने राज्य का नाम लिखकर भेजें:"
    elif lang == "mr":
        prompt = "📍 **पायरी 2/7: आपण कोणत्या राज्यात किंवा केंद्रशासित प्रदेशात राहता?**\n\nखालील पर्यायांमधून निवडा किंवा आपल्या राज्याचे नाव टाईप करा:"
    else:
        prompt = "📍 **Step 2 of 7: Which State or Union Territory do you currently reside in?**\n\nSelect below or type your state name:"

    await target_message.answer(
        text=prompt,
        reply_markup=get_state_keyboard(lang),
        parse_mode="Markdown",
    )


# ---------------- Step 2: State ----------------

@router.callback_query(F.data.startswith("state_"))
async def process_state_callback(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.answer()
    except Exception:
        pass
    state_val = callback.data.replace("state_", "")
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await state.update_data(state=state_val)
    await ask_age_question(callback.message, state, lang)


@router.message(CitizenInterview.waiting_for_state)
async def process_state_text(message: Message, state: FSMContext) -> None:
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    state_text = (message.text or "").strip().title()
    await state.update_data(state=state_text)
    await ask_age_question(message, state, lang)


async def ask_age_question(target_message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(CitizenInterview.waiting_for_age)
    if lang == "hi":
        prompt = "🎂 **चरण 3/7: आपकी आयु (उम्र) कितने वर्ष है?**\n\nआयु समूह चुनें या अपनी सटीक उम्र लिखें (उदा. 35):"
    elif lang == "mr":
        prompt = "🎂 **पायरी 3/7: आपले वय किती वर्षे आहे?**\n\nवयोगट निवडा किंवा आपले अचूक वय टाईप करा (उदा. 35):"
    else:
        prompt = "🎂 **Step 3 of 7: What is your age in years?**\n\nSelect an age group or type your exact age (e.g. 35):"

    await target_message.answer(
        text=prompt,
        reply_markup=get_age_keyboard(lang),
        parse_mode="Markdown",
    )


# ---------------- Step 3: Age ----------------

@router.callback_query(F.data.startswith("age_"))
async def process_age_callback(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.answer()
    except Exception:
        pass
    age_val = int(callback.data.replace("age_", ""))
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await state.update_data(age=age_val)
    await ask_gender_question(callback.message, state, lang)


@router.message(CitizenInterview.waiting_for_age)
async def process_age_text(message: Message, state: FSMContext) -> None:
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    match = re.search(r"\d+", message.text or "")
    age_val = int(match.group(0)) if match else 30
    await state.update_data(age=age_val)
    await ask_gender_question(message, state, lang)


async def ask_gender_question(target_message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(CitizenInterview.waiting_for_gender)
    if lang == "hi":
        prompt = "⚧ **चरण 4/7: कृपया अपना लिंग (Gender) चुनें:**"
    elif lang == "mr":
        prompt = "⚧ **पायरी 4/7: कृपया आपले लिंग निवडा:**"
    else:
        prompt = "⚧ **Step 4 of 7: Please select your gender:**"

    await target_message.answer(
        text=prompt,
        reply_markup=get_gender_keyboard(lang),
        parse_mode="Markdown",
    )


# ---------------- Step 4: Gender ----------------

@router.callback_query(F.data.startswith("gender_"))
async def process_gender_callback(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.answer()
    except Exception:
        pass
    gender_val = callback.data.replace("gender_", "")
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await state.update_data(gender=gender_val)
    await ask_occupation_question(callback.message, state, lang)


@router.message(CitizenInterview.waiting_for_gender)
async def process_gender_text(message: Message, state: FSMContext) -> None:
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    t = (message.text or "").strip().lower()
    if "fem" in t or "महिला" in t or "स्त्री" in t or "woman" in t:
        gender_val = "female"
    elif "male" in t or "पुरुष" in t or "man" in t:
        gender_val = "male"
    else:
        gender_val = "other"
    await state.update_data(gender=gender_val)
    await ask_occupation_question(message, state, lang)


async def ask_occupation_question(target_message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(CitizenInterview.waiting_for_occupation)
    if lang == "hi":
        prompt = "💼 **चरण 5/7: आपका मुख्य व्यवसाय या कार्य क्या है?**\n\nनीचे दिए गए विकल्पों में से चुनें या अपना काम लिखें:"
    elif lang == "mr":
        prompt = "💼 **पायरी 5/7: आपला मुख्य व्यवसाय किंवा काम काय आहे?**\n\nखालील पर्यायांमधून निवडा किंवा आपले काम टाईप करा:"
    else:
        prompt = "💼 **Step 5 of 7: What is your primary occupation or profession?**\n\nSelect below or type your profession:"

    await target_message.answer(
        text=prompt,
        reply_markup=get_occupation_keyboard(lang),
        parse_mode="Markdown",
    )


# ---------------- Step 5: Occupation ----------------

@router.callback_query(F.data.startswith("occ_"))
async def process_occ_callback(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.answer()
    except Exception:
        pass
    occ_val = callback.data.replace("occ_", "")
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await state.update_data(occupation=occ_val)
    await ask_income_question(callback.message, state, lang)


@router.message(CitizenInterview.waiting_for_occupation)
async def process_occ_text(message: Message, state: FSMContext) -> None:
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    occ_val = (message.text or "").strip().title()
    await state.update_data(occupation=occ_val)
    await ask_income_question(message, state, lang)


async def ask_income_question(target_message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(CitizenInterview.waiting_for_income)
    if lang == "hi":
        prompt = "💰 **चरण 6/7: आपकी अनुमानित वार्षिक पारिवारिक आय कितनी है?**\n\nआय का स्लैब चुनें या संख्या लिखें (उदा. 200000):"
    elif lang == "mr":
        prompt = "💰 **पायरी 6/7: आपले अंदाजे वार्षिक कौटुंबिक उत्पन्न किती आहे?**\n\nउत्पन्नाचा गट निवडा किंवा रक्कम टाईप करा (उदा. 200000):"
    else:
        prompt = "💰 **Step 6 of 7: What is your approximate annual family income?**\n\nSelect an income slab or type amount (e.g. 200000):"

    await target_message.answer(
        text=prompt,
        reply_markup=get_income_keyboard(lang),
        parse_mode="Markdown",
    )


# ---------------- Step 6: Income ----------------

@router.callback_query(F.data.startswith("inc_"))
async def process_income_callback(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.answer()
    except Exception:
        pass
    inc_val = float(callback.data.replace("inc_", ""))
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await state.update_data(annual_family_income=inc_val)
    await ask_category_question(callback.message, state, lang)


@router.message(CitizenInterview.waiting_for_income)
async def process_income_text(message: Message, state: FSMContext) -> None:
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    text = (message.text or "").lower().replace(",", "").replace("₹", "").replace("inr", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(lakh|lakhs|lac|l)?", text)
    if match:
        val = float(match.group(1))
        if match.group(2):
            inc_val = val * 100000
        elif val < 100:
            inc_val = val * 100000
        else:
            inc_val = val
    else:
        inc_val = 200000.0
    await state.update_data(annual_family_income=inc_val)
    await ask_category_question(message, state, lang)


async def ask_category_question(target_message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(CitizenInterview.waiting_for_category)
    if lang == "hi":
        prompt = "🏷️ **चरण 7/7: आप किस सामाजिक वर्ग (Social Category) से संबंधित हैं?**"
    elif lang == "mr":
        prompt = "🏷️ **पायरी 7/7: आपण कोणत्या सामाजिक प्रवर्गाशी (Category) संबंधित आहात?**"
    else:
        prompt = "🏷️ **Step 7 of 7: Which social category do you belong to?**"

    await target_message.answer(
        text=prompt,
        reply_markup=get_category_keyboard(lang),
        parse_mode="Markdown",
    )


# ---------------- Step 7: Category & Assessment Completion ----------------

@router.callback_query(F.data.startswith("cat_"))
async def process_category_callback(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.answer()
    except Exception:
        pass
    cat_val = callback.data.replace("cat_", "")
    lang = get_user_language(callback.from_user.id) or DEFAULT_LANGUAGE
    await state.update_data(category=cat_val)
    await finalize_assessment(callback.message, callback.from_user.id, state, lang)


@router.message(CitizenInterview.waiting_for_category)
async def process_category_text(message: Message, state: FSMContext) -> None:
    lang = get_user_language(message.from_user.id) or DEFAULT_LANGUAGE
    t = (message.text or "").strip().upper()
    if "SC" in t:
        cat_val = "SC"
    elif "ST" in t:
        cat_val = "ST"
    elif "OBC" in t:
        cat_val = "OBC"
    elif "MIN" in t or "EWS" in t:
        cat_val = "Minority"
    else:
        cat_val = "General"
    await state.update_data(category=cat_val)
    await finalize_assessment(message, message.from_user.id, state, lang)


async def finalize_assessment(target_message: Message, user_id: int, state: FSMContext, lang: str) -> None:
    """Saves profile, runs recommendation engine, and displays results."""
    try:
        data = await state.get_data()
        await state.clear()

        full_name = data.get("full_name") or ("नागरिक" if lang != "en" else "Citizen")
        state_name = data.get("state") or "all"
        age = data.get("age", 30)
        gender = data.get("gender", "male")
        occ = data.get("occupation", "Worker")
        income = data.get("annual_family_income", 200000.0)
        category = data.get("category", "General")

        # Construct and save profile
        profile = CitizenProfile(
            user_id=str(user_id),
            full_name=full_name,
            language=lang,
            state=state_name,
            age=age,
            gender=gender,
            occupation=occ,
            annual_family_income=income,
            category=category,
        )

        repo = CitizenProfileRepository()
        repo.save_profile(profile)

        # Evaluate recommendations
        scheme_repo = SchemeRepository()
        rec_service = RecommendationService(scheme_repo)
        recs = rec_service.get_recommendations_for_profile(profile)
        eligible_schemes = [r for r in recs if r.overall_status == "ELIGIBLE"]
        verify_schemes = [r for r in recs if r.overall_status == "NEEDS_VERIFICATION"]

        # Initialize conversational context with top recommended scheme
        displayed_schemes = (eligible_schemes[:4] if eligible_schemes else verify_schemes[:4])
        ctx_repo = ConversationContextRepository()
        if displayed_schemes:
            top_scheme = displayed_schemes[0]
            ctx_repo.set_active_scheme(str(user_id), top_scheme.scheme_id, top_scheme.scheme_name)
            ctx_repo.add_turn(
                str(user_id),
                "system",
                f"Assessment completed. Top recommendation: {top_scheme.scheme_name}",
                top_scheme.scheme_id,
            )
        if lang == "hi":
            res_text = (
                f"✅ **प्रोफाइल सफलतापूर्वक तैयार हो गई है!**\n\n"
                f"📋 **आपकी प्रोफाइल जानकारी:**\n"
                f"• **नाम:** {full_name}\n"
                f"• **राज्य:** {state_name}\n"
                f"• **आयु:** {age} वर्ष | **लिंग:** {gender.title()}\n"
                f"• **व्यवसाय:** {occ}\n"
                f"• **वार्षिक आय:** ₹{income:,.0f}\n"
                f"• **वर्ग:** {category}\n\n"
                f"🎯 **आपके लिए उच्च प्राथमिकता वाली योजनाएँ (Eligible):**\n"
            )
        elif lang == "mr":
            res_text = (
                f"✅ **आपली प्रोफाइल यशस्वीरित्या पूर्ण झाली आहे!**\n\n"
                f"📋 **आपली नोंदवलेली माहिती:**\n"
                f"• **नाव:** {full_name}\n"
                f"• **राज्य:** {state_name}\n"
                f"• **वय:** {age} वर्षे | **लिंग:** {gender.title()}\n"
                f"• **व्यवसाय:** {occ}\n"
                f"• **वार्षिक उत्पन्न:** ₹{income:,.0f}\n"
                f"• **प्रवर्ग:** {category}\n\n"
                f"🎯 **आपल्यासाठी पात्र असणाऱ्या प्रमुख शासकीय योजना (Eligible):**\n"
            )
        else:
            res_text = (
                f"✅ **Profile Assessment Completed Successfully!**\n\n"
                f"📋 **Your Verified Profile:**\n"
                f"• **Name:** {full_name}\n"
                f"• **State/UT:** {state_name}\n"
                f"• **Age:** {age} yrs | **Gender:** {gender.title()}\n"
                f"• **Occupation:** {occ}\n"
                f"• **Family Income:** ₹{income:,.0f}/yr\n"
                f"• **Category:** {category}\n\n"
                f"🎯 **Schemes You Are Eligible For (High Match):**\n"
            )

        # Add top eligible schemes
        displayed_schemes = (eligible_schemes[:4] if eligible_schemes else verify_schemes[:4])
        if displayed_schemes:
            for r in displayed_schemes:
                s_rec = scheme_repo.get_scheme_by_id(r.scheme_id)
                url = (s_rec.official_scheme_url if s_rec and s_rec.official_scheme_url else "https://myscheme.gov.in")
                benefit = r.benefit_summary or (s_rec.benefit_amount if s_rec else "Direct Government Benefit")
                if lang == "hi":
                    res_text += f"\n🏛️ **{r.scheme_name}**\n   💰 *लाभ:* {benefit}\n   🔗 [आधिकारिक पोर्टल]({url})\n"
                elif lang == "mr":
                    res_text += f"\n🏛️ **{r.scheme_name}**\n   💰 *लाभ:* {benefit}\n   🔗 [अधिकृत संकेतस्थळ]({url})\n"
                else:
                    res_text += f"\n🏛️ **{r.scheme_name}**\n   💰 *Benefit:* {benefit}\n   🔗 [Official Portal]({url})\n"
        else:
            res_text += "• Pan-India Central welfare schemes are being matched for your category.\n"

        # Add required documents checklist
        if lang == "hi":
            res_text += (
                "\n📄 **आवेदन हेतु आवश्यक मुख्य दस्तावेज:**\n"
                "• आधार कार्ड (Aadhaar Card)\n"
                "• बैंक पासबुक (DBT सक्रिय बैंक खाता)\n"
                "• आय/जाति प्रमाण पत्र (यदि लागू हो)\n"
                "• पासपोर्ट साइज फोटो व मोबाइल नंबर\n\n"
                "💬 **आप इन योजनाओं के बारे में कोई भी प्रश्न पूछ सकते हैं!**\n"
                "उदा. लिखें: *'PM-KISAN के लिए कैसे आवेदन करें?'* या *'KCC के क्या दस्तावेज चाहिए?'*"
            )
        elif lang == "mr":
            res_text += (
                "\n📄 **अर्जासाठी आवश्यक मुख्य कागदपत्रे:**\n"
                "• आधार कार्ड (Aadhaar Card)\n"
                "• बँक पासबुक (DBT लिंक असलेले बँक खाते)\n"
                "• उत्पन्न/जात प्रमाणपत्र (लागू असल्यास)\n"
                "• पासपोर्ट साईज फोटो आणि मोबाईल नंबर\n\n"
                "💬 **आपण आता मला या योजनांबद्दल कोणताही प्रश्न विचारू शकता!**\n"
                "उदा. विचारा: *'PM-KISAN चा लाभ कसा मिळवायचा?'* किंवा *'KCC साठी काय कागदपत्रे लागतात?'*"
            )
        else:
            res_text += (
                "\n📄 **Key Documents You Will Need:**\n"
                "• Aadhaar Card (Identity proof)\n"
                "• Bank Passbook (DBT-enabled bank account)\n"
                "• Income/Caste Certificate (if applicable)\n"
                "• Passport photo & mobile number linked with Aadhaar\n\n"
                "💬 **You can now ask me any follow-up question!**\n"
                "Try asking: *'How do I apply for PM-KISAN?'* or *'What documents are needed for KCC?'*"
            )

        try:
            await target_message.answer(
                text=res_text,
                reply_markup=get_assessment_completion_keyboard(lang),
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
        except Exception:
            await target_message.answer(
                text=res_text,
                reply_markup=get_assessment_completion_keyboard(lang),
                disable_web_page_preview=True,
            )
    except Exception as e:
        logger.error(f"Error in finalize_assessment: {e}", exc_info=True)
        try:
            fallback = "✅ Profile assessment saved! Use the menu below to explore schemes." if lang == "en" else "✅ प्रोफाइल सुरक्षित कर ली गई है! नीचे दिए गए विकल्पों से योजनाएं देखें।"
            await target_message.answer(text=fallback, reply_markup=get_assessment_completion_keyboard(lang))
        except Exception:
            pass
