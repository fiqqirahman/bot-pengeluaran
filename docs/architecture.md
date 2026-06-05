# Architecture

## Overview

Local-only Telegram bot for recording personal expenses. Runs on the user's laptop using Telegram polling (no webhook needed). Data is persisted in a local PostgreSQL database.

## Tech Stack

| Component         | Technology              |
|-------------------|-------------------------|
| Language          | Python 3.9+             |
| Telegram          | python-telegram-bot 21+ |
| Database          | PostgreSQL (psycopg 3)  |
| Env Loading       | python-dotenv           |
| Testing           | pytest                  |

## Project Structure

```
bot-pengeluaran/
├── pyproject.toml              # Dependencies & pytest config
├── .env.example                # Required env vars template
├── README.md                   # Setup & usage
├── AGENTS.md                   # AI agent guidance
├── sql/
│   └── 001_create_expenses.sql # DB migration
├── src/expense_bot/
│   ├── __init__.py             # Package marker
│   ├── __main__.py             # Entrypoint: python -m expense_bot
│   ├── config.py               # ✅ Env loading & validation
│   ├── models.py               # Shared dataclasses
│   ├── parser.py               # Free-form text → ParsedExpense
│   ├── categorizer.py          # Keyword-based category guessing
│   ├── analysis.py             # Summary & top-expense calculations
│   ├── repository.py           # Postgres CRUD operations
│   └── telegram_app.py         # Command handlers & message routing
├── tests/
│   ├── test_config.py          # ✅ Config tests
│   ├── test_parser.py          # Parser tests
│   ├── test_categorizer.py     # Categorizer tests
│   └── test_analysis.py        # Analysis tests
└── docs/
    ├── architecture.md         # This file
    ├── features.md             # Feature documentation
    ├── database.md             # Data model & SQL
    └── api.md                  # Telegram commands & user interaction
```

✅ = Implemented

## Module Responsibilities

### config.py ✅
- Loads `TELEGRAM_BOT_TOKEN` and `DATABASE_URL` from `.env`
- Validates both are present, raises `RuntimeError` if missing
- Returns frozen `Config` dataclass

### models.py (planned)
- `ParsedExpense`: description, amount, category (optional), raw_text
- `ExpenseRecord`: full DB record with id, telegram_user_id, timestamps

### parser.py (planned)
- `parse_expense(text) -> ParsedExpense`: extract amount & description
- `parse_month_arg(arg) -> (year, month)`: parse `/summary 2026-05`
- Amount formats: `35000`, `25rb`, `25k`

### categorizer.py (planned)
- `guess_category(description) -> str`: keyword-based guessing
- Returns `"uncategorized"` if no match

### analysis.py (planned)
- `monthly_summary(records) -> dict`: total, category breakdown
- `top_expenses(records, limit) -> list`: largest N expenses

### repository.py (planned)
- CRUD operations against Postgres `expenses` table
- Scopes all queries by `telegram_user_id`

### telegram_app.py (planned)
- Builds `Application` with all handlers
- Registers commands: `/summary`, `/top`, `/recent`, `/category`, `/edit`, `/delete_last`, `/delete`
- Routes free-form messages to parser → categorizer → repository

## Data Flow

### Recording an Expense
```
User sends: "makan siang 35000"
  ↓
Telegram API → Bot receives message update
  ↓
parser.parse_expense(text) → ParsedExpense(desc="makan siang", amount=35000)
  ↓
categorizer.guess_category(desc) → "food"
  ↓
repository.insert(record) → ExpenseRecord with id=1
  ↓
Bot replies: "Tersimpan #1: Rp35.000 - makan siang (food)"
```

### Running Analysis
```
User sends: /summary 2026-05
  ↓
parser.parse_month_arg("2026-05") → (2026, 5)
  ↓
repository.get_by_month(user_id, 2026, 5) → [ExpenseRecord, ...]
  ↓
analysis.monthly_summary(records) → {total: 350000, categories: {...}}
  ↓
Bot replies with formatted summary
```

## Design Decisions

1. **Polling over webhook**: No public URL needed, runs on laptop
2. **Single table**: Keeps v1 simple, queries straightforward
3. **Pure logic separated**: parser/categorizer/analysis are testable without Telegram or DB
4. **Frozen dataclasses**: Prevent accidental mutation
5. **User-scoped queries**: All DB operations filter by `telegram_user_id`
6. **Indonesian shorthand**: Support `25rb` and `25k` for amounts
7. **Keyword-based categories**: Simple rules, easy to extend
