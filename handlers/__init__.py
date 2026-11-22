"""
Handlers package initialization.
Registers all modular routers into the main dispatcher.
Order:
1. language_router (for language commands and language selection callbacks)
2. start_router (for /start, main menu, assessment launch buttons, and guided interview FSM)
3. help_router (for /help, RAG scheme intelligence, and follow-up Q&A)
"""

from aiogram import Dispatcher
from .language import router as language_router
from .start import router as start_router
from .help import router as help_router


def register_handlers(dp: Dispatcher) -> None:
    """Register all routers in order."""
    dp.include_router(language_router)
    dp.include_router(start_router)
    dp.include_router(help_router)
