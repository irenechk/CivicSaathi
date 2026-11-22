"""
Configuration management for Civicsaathi Bot.
Loads environment variables securely using python-dotenv and Pydantic.
Ensures tokens and secrets are never printed or logged in plaintext.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, ValidationError

# Locate base directory and load .env file
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# Explicitly load .env from the project directory
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


class Settings(BaseModel):
    """
    Application settings model with secret masking and validation.
    """
    telegram_bot_token: SecretStr = Field(..., alias="TELEGRAM_BOT_TOKEN")
    openai_api_key: SecretStr = Field(default=SecretStr(""), alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")

    @property
    def bot_token(self) -> str:
        """Returns the unmasked Telegram Bot Token for internal client usage only."""
        return self.telegram_bot_token.get_secret_value()

    @property
    def api_key(self) -> str:
        """Returns the unmasked OpenAI API Key for internal client usage only."""
        return self.openai_api_key.get_secret_value()

    def __repr__(self) -> str:
        # Prevent accidental secret exposure in debug logs or repr calls
        return f"Settings(telegram_bot_token=**********, openai_api_key=**********, openai_model='{self.openai_model}')"

    def __str__(self) -> str:
        return self.__repr__()


def load_config() -> Settings:
    """
    Load and validate configuration from environment variables.
    Exits with a clear, user-friendly error message if required keys are missing or placeholders.
    """
    raw_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    placeholder_tokens = {
        "",
        "your_telegram_bot_token_here",
        "YOUR_BOT_TOKEN",
        "PUT_YOUR_TOKEN_HERE",
    }

    if not raw_token or raw_token in placeholder_tokens:
        print("\n" + "=" * 65, file=sys.stderr)
        print("❌ CONFIGURATION ERROR: TELEGRAM_BOT_TOKEN is missing or not configured!", file=sys.stderr)
        print("=" * 65, file=sys.stderr)
        print("Civicsaathi requires a valid Telegram Bot Token to start.", file=sys.stderr)
        print("\nHow to configure your token:", file=sys.stderr)
        print(f"1. Open the '.env' file in the project root: {ENV_PATH}", file=sys.stderr)
        print("2. Set your Telegram token obtained from @BotFather:", file=sys.stderr)
        print("   TELEGRAM_BOT_TOKEN=<your_actual_bot_token>", file=sys.stderr)
        print("3. See '.env.example' for reference.", file=sys.stderr)
        print("=" * 65 + "\n", file=sys.stderr)
        sys.exit(1)

    try:
        settings = Settings(
            TELEGRAM_BOT_TOKEN=raw_token,
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", "").strip(),
            OPENAI_MODEL=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
        )
        return settings
    except ValidationError as err:
        print("\n" + "=" * 65, file=sys.stderr)
        print("❌ CONFIGURATION VALIDATION ERROR:", file=sys.stderr)
        print("=" * 65, file=sys.stderr)
        for error in err.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            print(f"- {field}: {error['msg']}", file=sys.stderr)
        print("=" * 65 + "\n", file=sys.stderr)
        sys.exit(1)
