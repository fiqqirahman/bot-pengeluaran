from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    database_url: str


def load_config() -> Config:
    load_dotenv()

    telegram_bot_token = getenv("TELEGRAM_BOT_TOKEN")
    database_url = getenv("DATABASE_URL")

    missing = []
    if not telegram_bot_token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not database_url:
        missing.append("DATABASE_URL")
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    return Config(
        telegram_bot_token=telegram_bot_token,
        database_url=database_url,
    )
