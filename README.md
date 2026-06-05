# Bot Pengeluaran

Local Telegram bot for recording personal expenses and analyzing the biggest spending categories.

## Local Setup

1. Create and activate a virtual environment.
2. Install the project:

```bash
pip install -e ".[dev]"
```

3. Copy `.env.example` to `.env`.
4. Put your Telegram bot token in `TELEGRAM_BOT_TOKEN`.
5. Set `DATABASE_URL` for your local Postgres database.

## Database

Create the database locally:

```bash
createdb bot_pengeluaran
psql bot_pengeluaran -f sql/001_create_expenses.sql
```

## Run

```bash
python -m expense_bot
```

## Test

```bash
pytest
```
