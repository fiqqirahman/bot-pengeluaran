import pytest

from expense_bot.config import Config, load_config


def test_load_config_reads_required_environment(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/expenses")

    config = load_config()

    assert config == Config(
        telegram_bot_token="123:abc",
        database_url="postgresql://localhost/expenses",
    )


def test_load_config_rejects_missing_telegram_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/expenses")

    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        load_config()


def test_load_config_rejects_missing_database_url(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        load_config()
