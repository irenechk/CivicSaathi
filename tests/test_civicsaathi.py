"""
Test suite for Civicsaathi Phase 2: Multilingual Chatbot Experience.
Verifies language selection, SQLite persistence, translation completeness, and main menu keyboards.
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.db import (
    init_db,
    get_user_language,
    set_user_language,
    delete_user_language,
)
from services.i18n import (
    SUPPORTED_LANGUAGES,
    INITIAL_LANGUAGE_PROMPT,
    LANGUAGE_CHANGE_PROMPT,
    STRINGS,
    get_text,
)
from handlers.language import get_language_keyboard
from handlers.start import get_main_menu_keyboard
from handlers import register_handlers
from aiogram import Dispatcher


def test_supported_languages_list():
    """Verify exactly 3 languages are supported: en, hi, mr."""
    assert set(SUPPORTED_LANGUAGES.keys()) == {"en", "hi", "mr"}
    assert "English" in SUPPORTED_LANGUAGES["en"]["name"]
    assert "Hindi" in SUPPORTED_LANGUAGES["hi"]["name"]
    assert "Marathi" in SUPPORTED_LANGUAGES["mr"]["name"]


def test_initial_language_prompt():
    """Verify exact prompt required when starting for the first time."""
    expected_prompt = (
        "Namaste! Welcome to Civicsaathi 🇮🇳\n\n"
        "Before we begin, please choose your preferred language."
    )
    assert INITIAL_LANGUAGE_PROMPT == expected_prompt


def test_language_keyboard_buttons():
    """Verify the 3 inline buttons: English, हिंदी, मराठी."""
    keyboard = get_language_keyboard()
    flat_buttons = [button for row in keyboard.inline_keyboard for button in row]
    texts = [b.text for b in flat_buttons]
    callbacks = [b.callback_data for b in flat_buttons]

    assert any("English" in t for t in texts)
    assert any("हिंदी" in t for t in texts)
    assert any("मराठी" in t for t in texts)

    assert "setlang_en" in callbacks
    assert "setlang_hi" in callbacks
    assert "setlang_mr" in callbacks


def test_sqlite_language_persistence():
    """Verify storing, retrieving, updating, and persisting user language."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        db_path = Path(tmp.name)
        init_db(db_path)

        user_id = 987654321

        # 1. New user has no language set
        assert get_user_language(user_id, db_path) is None

        # 2. User selects Hindi
        set_user_language(user_id, "hi", db_path)
        assert get_user_language(user_id, db_path) == "hi"

        # 3. User switches to Marathi
        set_user_language(user_id, "mr", db_path)
        assert get_user_language(user_id, db_path) == "mr"

        # 4. User switches to English
        set_user_language(user_id, "en", db_path)
        assert get_user_language(user_id, db_path) == "en"

        # 5. Persistence across new connection
        assert get_user_language(user_id, db_path) == "en"


def test_translations_completeness():
    """Verify all 3 languages have complete translations for all required UI keys."""
    required_keys = [
        "welcome_back",
        "lang_confirmed",
        "btn_schemes",
        "btn_profile",
        "btn_recommended",
        "btn_documents",
        "btn_helpline",
        "btn_language",
        "btn_help",
        "schemes_response",
        "profile_response",
        "recommended_response",
        "documents_response",
        "helpline_response",
        "help_text",
        "unknown_text",
    ]

    for lang in ["en", "hi", "mr"]:
        for key in required_keys:
            val = get_text(key, lang)
            assert val and not val.startswith(f"[{key}]"), f"Missing translation for key '{key}' in '{lang}'"


def test_main_menu_7_buttons():
    """Verify main menu has all 7 buttons in English, Hindi, and Marathi."""
    for lang in ["en", "hi", "mr"]:
        keyboard = get_main_menu_keyboard(lang)
        flat_buttons = [button for row in keyboard.inline_keyboard for button in row]
        callbacks = [b.callback_data for b in flat_buttons]

        assert len(flat_buttons) == 7, f"Main menu in '{lang}' must have exactly 7 buttons"

        # Check that all 7 callbacks are present
        expected_callbacks = {
            "menu_schemes",
            "menu_profile",
            "menu_recommended",
            "menu_documents",
            "menu_helpline",
            "menu_language",
            "menu_help",
        }
        assert set(callbacks) == expected_callbacks


def test_dispatcher_registers_all_routers():
    """Verify dispatcher includes language, start, and help routers."""
    dp = Dispatcher()
    register_handlers(dp)
    assert len(dp.sub_routers) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
