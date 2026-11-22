"""
Civicsaathi Telegram Bot — Main Application Entry Point.
Phase 2: Multilingual Chatbot Experience (English, Hindi, Marathi).

Handles:
- Startup validation & configuration loading
- SQLite database initialization for language persistence
- Safe dual logging (stdout + logs/bot.log)
- Telegram connection setup and error handling
- Graceful shutdown on termination signals
- Local polling
"""

import asyncio
import logging
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from config import load_config
from services.db import init_db
from handlers import register_handlers

# Ensure logs directory exists and configure secure dual logging (stdout + logs/bot.log)
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "bot.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)

# Suppress verbose internal logs while preserving error visibility
logging.getLogger("aiogram.event").setLevel(logging.WARNING)
logger = logging.getLogger("civicsaathi.bot")


async def main() -> None:
    """Main application loop."""
    logger.info("Initializing Civicsaathi Bot (Phase 2: Multilingual Experience)...")

    # 1. Load and validate configuration
    config = load_config()
    logger.info("Configuration validated successfully. (Secrets safely masked)")

    # 2. Initialize SQLite persistence layer
    init_db()
    logger.info("Database initialized successfully (SQLite).")

    # 3. Initialize Bot instance
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # 4. Initialize Dispatcher with FSM in-memory storage and register handler routers
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp)
    logger.info("Message handlers, FSM interview, and multilingual callback routers registered.")

    # 5. Verify Telegram API connection and bot identity
    try:
        bot_info = await bot.get_me()
        logger.info(
            "Telegram connection verified: Logged in as @%s (Name: '%s', ID: %s)",
            bot_info.username,
            bot_info.first_name,
            bot_info.id,
        )
    except TelegramAPIError as err:
        logger.error(
            "Failed to connect to Telegram API. Please verify your token: %s",
            err.message,
        )
        await bot.session.close()
        sys.exit(1)
    except Exception as err:
        logger.error("Unexpected error connecting to Telegram API: %s", err)
        await bot.session.close()
        sys.exit(1)

    # 6. Start Polling with clean update queue
    try:
        # Drop any pending updates accumulated while offline to prevent stale spam
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Civicsaathi Bot is active and listening for updates (Polling mode)...")
        print("\n" + "=" * 65)
        print(f"🤖 Civicsaathi Bot is live! Username: @{bot_info.username}")
        print("🌐 Multilingual Support Enabled: English 🇬🇧 | हिंदी 🇮🇳 | मराठी 🇮🇳")
        print("Press Ctrl+C to stop.")
        print("=" * 65 + "\n")

        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received termination signal. Shutting down gracefully...")
    except TelegramAPIError as err:
        logger.error("Telegram runtime error: %s", err.message)
    except Exception as err:
        logger.exception("Unexpected runtime error occurred: %s", err)
    finally:
        logger.info("Closing Telegram bot session...")
        await bot.session.close()
        logger.info("Civicsaathi Bot shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Civicsaathi Bot stopped.")
