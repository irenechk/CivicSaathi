"""
Language selection and management handlers for Civicsaathi.
Handles /language command and language selection callbacks.
Seamlessly routes first-time citizens into the guided interview onboarding.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
)

from services.db import set_user_language, get_user_language
from services.i18n import (
    INITIAL_LANGUAGE_PROMPT,
    LANGUAGE_CHANGE_PROMPT,
    get_text,
    is_valid_language,
)
from database.repository import CitizenProfileRepository

router = Router(name="language_router")


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Builds the 3-language inline selection keyboard."""
    buttons = [
        [
            InlineKeyboardButton(text="English 🇬🇧", callback_data="setlang_en"),
        ],
        [
            InlineKeyboardButton(text="हिंदी 🇮🇳", callback_data="setlang_hi"),
        ],
        [
            InlineKeyboardButton(text="मराठी 🇮🇳", callback_data="setlang_mr"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("language"))
async def handle_language_command(message: Message) -> None:
    """Handles the /language command to switch language at any time."""
    await message.answer(
        text=LANGUAGE_CHANGE_PROMPT,
        reply_markup=get_language_keyboard(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("setlang_"))
async def handle_language_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handles user tapping a language button.
    Persists preference to SQLite and routes to interview or main menu.
    """
    if not callback.data:
        return

    lang_code = callback.data.replace("setlang_", "")
    if not is_valid_language(lang_code):
        lang_code = "en"

    # Persist selected language
    set_user_language(callback.from_user.id, lang_code)
    await callback.answer()

    # Check whether the citizen already has completed their profile
    profile_repo = CitizenProfileRepository()
    profile = profile_repo.get_profile(str(callback.from_user.id))
    has_profile = profile is not None and (profile.age is not None or profile.occupation is not None)

    confirmation_text = get_text("lang_confirmed", lang_code)
    if callback.message:
        await callback.message.answer(
            text=confirmation_text,
            parse_mode="Markdown",
        )

    if not has_profile and callback.message:
        # First-time onboarding: immediately start Step 1 (Name)
        from handlers.interview import start_interview_flow
        await start_interview_flow(callback.message, state, lang_code)
    elif callback.message:
        # Existing user returning or switching language: show main menu
        from handlers.start import get_main_menu_keyboard
        welcome_text = get_text("welcome_back", lang_code)
        await callback.message.answer(
            text=welcome_text,
            reply_markup=get_main_menu_keyboard(lang_code),
        )
