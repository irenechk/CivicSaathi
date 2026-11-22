"""
Live Telegram connectivity test script.
Verifies credentials directly with Telegram API servers.
"""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import load_config
from aiogram import Bot


async def verify_telegram():
    print("Verifying Telegram Bot API credentials...")
    config = load_config()
    bot = Bot(token=config.bot_token)
    try:
        me = await bot.get_me()
        print("\n✅ TELEGRAM CONNECTION SUCCESSFUL!")
        print(f"   • Bot ID:       {me.id}")
        print(f"   • Bot Username: @{me.username}")
        print(f"   • Bot Name:     {me.first_name}")
        print(f"   • Can Join Grp: {me.can_join_groups}")
        print("Telegram API accepted the bot token without issues.\n")
        return True
    except Exception as e:
        print(f"\n❌ FAILED TO CONNECT TO TELEGRAM: {e}\n", file=sys.stderr)
        return False
    finally:
        await bot.session.close()


if __name__ == "__main__":
    success = asyncio.run(verify_telegram())
    sys.exit(0 if success else 1)
