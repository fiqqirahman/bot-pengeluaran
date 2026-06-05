# Telegram Expense Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Telegram bot that records free-form expense messages into local Postgres and returns monthly spending analysis.

**Architecture:** Use a small Python package split into parser, categorizer, repository, analysis, config, and Telegram app modules. Keep pure parsing and analysis logic independent from Telegram and Postgres so most behavior is testable without external services. Use Telegram polling for local laptop operation and Postgres for persisted expense records.

**Tech Stack:** Python 3, `python-telegram-bot`, `psycopg`, `python-dotenv`, Postgres, `pytest`.

---

## File Structure

- `pyproject.toml`: Project metadata, runtime dependencies, pytest configuration.
- `.env.example`: Documents required local environment variables without secrets.
- `README.md`: Local setup, database setup, bot run, and test instructions.
- `sql/001_create_expenses.sql`: Postgres table creation script.
- `src/expense_bot/__init__.py`: Package marker.
- `src/expense_bot/models.py`: Shared dataclasses for parsed expenses and expense records.
- `src/expense_bot/parser.py`: Free-form text parsing and month argument parsing.
- `src/expense_bot/categorizer.py`: Keyword-based category guessing.
- `src/expense_bot/analysis.py`: Summary and top-expense calculations from records.
- `src/expense_bot/config.py`: Environment loading and validation.
- `src/expense_bot/repository.py`: Postgres persistence functions.
- `src/expense_bot/telegram_app.py`: Telegram command handlers and message routing.
- `src/expense_bot/__main__.py`: `python -m expense_bot` entrypoint.
- `tests/test_parser.py`: Parser tests.
- `tests/test_categorizer.py`: Categorizer tests.
- `tests/test_analysis.py`: Analysis tests.

## Task 1: Project Skeleton And Configuration

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `README.md`
- Create: `src/expense_bot/__init__.py`
- Create: `src/expense_bot/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing config tests**

Create `tests/test_config.py`:

```python
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
```

- [ ] **Step 2: Add minimal project metadata**

Create `pyproject.toml`:

```toml
[project]
name = "bot-pengeluaran"
version = "0.1.0"
description = "Local Telegram bot for tracking personal expenses"
requires-python = ">=3.11"
dependencies = [
    "psycopg[binary]>=3.2.0",
    "python-dotenv>=1.0.1",
    "python-telegram-bot>=21.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Create `src/expense_bot/__init__.py`:

```python
"""Local Telegram expense tracking bot."""
```

- [ ] **Step 3: Run test to verify it fails because config is missing**

Run: `pytest tests/test_config.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'expense_bot.config'`.

- [ ] **Step 4: Implement config loading**

Create `src/expense_bot/config.py`:

```python
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
```

- [ ] **Step 5: Add local environment example and README setup**

Create `.env.example`:

```dotenv
TELEGRAM_BOT_TOKEN=replace-with-your-bot-token
DATABASE_URL=postgresql://localhost:5432/bot_pengeluaran
```

Create `README.md`:

```markdown
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
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`

Expected: PASS for all 3 tests.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .env.example README.md src/expense_bot/__init__.py src/expense_bot/config.py tests/test_config.py
git commit -m "feat: add project skeleton and config"
```

## Task 2: Expense Parser

**Files:**
- Create: `src/expense_bot/models.py`
- Create: `src/expense_bot/parser.py`
- Test: `tests/test_parser.py`

- [ ] **Step 1: Write failing parser tests**

Create `tests/test_parser.py`:

```python
from datetime import date

import pytest

from expense_bot.parser import ParseError, parse_expense_message, parse_month_arg


def test_parse_plain_number_expense_without_category():
    parsed = parse_expense_message("makan siang 35000")

    assert parsed.description == "makan siang"
    assert parsed.amount == 35000
    assert parsed.explicit_category is None
    assert parsed.raw_text == "makan siang 35000"


def test_parse_expense_with_trailing_category():
    parsed = parse_expense_message("gojek 18000 transport")

    assert parsed.description == "gojek"
    assert parsed.amount == 18000
    assert parsed.explicit_category == "transport"


def test_parse_indonesian_rb_amount():
    parsed = parse_expense_message("kopi 25rb")

    assert parsed.description == "kopi"
    assert parsed.amount == 25000
    assert parsed.explicit_category is None


def test_parse_k_amount():
    parsed = parse_expense_message("kopi 25k")

    assert parsed.description == "kopi"
    assert parsed.amount == 25000


def test_parse_rejects_text_without_amount():
    with pytest.raises(ParseError, match="nominal"):
        parse_expense_message("makan siang")


def test_parse_current_month_when_arg_empty():
    assert parse_month_arg("", today=date(2026, 6, 5)) == (2026, 6)


def test_parse_specific_month():
    assert parse_month_arg("2026-05", today=date(2026, 6, 5)) == (2026, 5)


def test_parse_rejects_invalid_month():
    with pytest.raises(ParseError, match="YYYY-MM"):
        parse_month_arg("mei", today=date(2026, 6, 5))
```

- [ ] **Step 2: Run parser tests to verify they fail**

Run: `pytest tests/test_parser.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'expense_bot.parser'`.

- [ ] **Step 3: Create shared models**

Create `src/expense_bot/models.py`:

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ParsedExpense:
    description: str
    amount: int
    explicit_category: str | None
    raw_text: str


@dataclass(frozen=True)
class ExpenseRecord:
    id: int
    telegram_user_id: int
    description: str
    amount: int
    category: str
    raw_text: str
    spent_at: datetime
```

- [ ] **Step 4: Implement parser**

Create `src/expense_bot/parser.py`:

```python
import re
from datetime import date

from expense_bot.models import ParsedExpense


class ParseError(ValueError):
    pass


_AMOUNT_RE = re.compile(r"(?<!\w)(\d+(?:[.,]\d+)?)(rb|k)?(?!\w)", re.IGNORECASE)
_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")


def parse_expense_message(text: str) -> ParsedExpense:
    raw_text = text.strip()
    match = _AMOUNT_RE.search(raw_text)
    if not match:
        raise ParseError("Tidak menemukan nominal. Contoh: makan siang 35000")

    amount = _parse_amount(match.group(1), match.group(2))
    before = raw_text[: match.start()].strip()
    after = raw_text[match.end() :].strip()

    explicit_category = after.lower() if after else None
    description = before
    if not description:
        raise ParseError("Deskripsi pengeluaran tidak boleh kosong.")

    return ParsedExpense(
        description=description,
        amount=amount,
        explicit_category=explicit_category,
        raw_text=raw_text,
    )


def parse_month_arg(arg: str, today: date | None = None) -> tuple[int, int]:
    clean_arg = arg.strip()
    if not clean_arg:
        current = today or date.today()
        return current.year, current.month

    match = _MONTH_RE.match(clean_arg)
    if not match:
        raise ParseError("Format bulan harus YYYY-MM, contoh: 2026-05")

    year = int(match.group(1))
    month = int(match.group(2))
    if month < 1 or month > 12:
        raise ParseError("Format bulan harus YYYY-MM, contoh: 2026-05")

    return year, month


def _parse_amount(number_text: str, suffix: str | None) -> int:
    normalized = number_text.replace(",", ".")
    value = float(normalized)
    if suffix and suffix.lower() in {"rb", "k"}:
        value *= 1000
    return int(value)
```

- [ ] **Step 5: Run parser tests to verify they pass**

Run: `pytest tests/test_parser.py -v`

Expected: PASS for all 8 tests.

- [ ] **Step 6: Commit**

```bash
git add src/expense_bot/models.py src/expense_bot/parser.py tests/test_parser.py
git commit -m "feat: parse expense messages"
```

## Task 3: Categorizer

**Files:**
- Create: `src/expense_bot/categorizer.py`
- Test: `tests/test_categorizer.py`

- [ ] **Step 1: Write failing categorizer tests**

Create `tests/test_categorizer.py`:

```python
from expense_bot.categorizer import choose_category, guess_category


def test_explicit_category_wins():
    assert choose_category("gojek", "custom") == "custom"


def test_guess_food_category_from_keywords():
    assert guess_category("kopi susu") == "food"


def test_guess_transport_category_from_keywords():
    assert guess_category("gojek ke kantor") == "transport"


def test_guess_uncategorized_when_no_keyword_matches():
    assert guess_category("iuran random") == "uncategorized"
```

- [ ] **Step 2: Run categorizer tests to verify they fail**

Run: `pytest tests/test_categorizer.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'expense_bot.categorizer'`.

- [ ] **Step 3: Implement categorizer**

Create `src/expense_bot/categorizer.py`:

```python
CATEGORY_KEYWORDS = {
    "food": ["makan", "kopi", "ayam", "nasi", "resto", "bakso", "mie", "minum"],
    "transport": ["gojek", "grab", "taxi", "bensin", "parkir", "tol"],
    "utilities": ["token", "listrik", "internet", "pulsa", "air"],
    "shopping": ["beli", "tokopedia", "shopee", "laundry"],
    "health": ["obat", "dokter", "apotek", "vitamin"],
}


def choose_category(description: str, explicit_category: str | None) -> str:
    if explicit_category:
        return explicit_category.strip().lower()
    return guess_category(description)


def guess_category(description: str) -> str:
    normalized = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    return "uncategorized"
```

- [ ] **Step 4: Run categorizer tests to verify they pass**

Run: `pytest tests/test_categorizer.py -v`

Expected: PASS for all 4 tests.

- [ ] **Step 5: Commit**

```bash
git add src/expense_bot/categorizer.py tests/test_categorizer.py
git commit -m "feat: categorize expenses"
```

## Task 4: Analysis Service

**Files:**
- Create: `src/expense_bot/analysis.py`
- Test: `tests/test_analysis.py`

- [ ] **Step 1: Write failing analysis tests**

Create `tests/test_analysis.py`:

```python
from datetime import datetime

from expense_bot.analysis import build_summary, top_expenses
from expense_bot.models import ExpenseRecord


def record(id, description, amount, category):
    return ExpenseRecord(
        id=id,
        telegram_user_id=99,
        description=description,
        amount=amount,
        category=category,
        raw_text=f"{description} {amount}",
        spent_at=datetime(2026, 6, id, 12, 0, 0),
    )


def test_build_summary_totals_by_category_and_largest_transaction():
    records = [
        record(1, "kopi", 25000, "food"),
        record(2, "gojek", 18000, "transport"),
        record(3, "makan siang", 35000, "food"),
    ]

    summary = build_summary(records)

    assert summary.total == 78000
    assert summary.category_totals == {"food": 60000, "transport": 18000}
    assert summary.largest.id == 3


def test_build_summary_handles_empty_records():
    summary = build_summary([])

    assert summary.total == 0
    assert summary.category_totals == {}
    assert summary.largest is None


def test_top_expenses_orders_by_amount_descending_and_limits_results():
    records = [record(i, f"item {i}", i * 1000, "misc") for i in range(1, 13)]

    result = top_expenses(records, limit=3)

    assert [expense.id for expense in result] == [12, 11, 10]
```

- [ ] **Step 2: Run analysis tests to verify they fail**

Run: `pytest tests/test_analysis.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'expense_bot.analysis'`.

- [ ] **Step 3: Implement analysis service**

Create `src/expense_bot/analysis.py`:

```python
from dataclasses import dataclass

from expense_bot.models import ExpenseRecord


@dataclass(frozen=True)
class ExpenseSummary:
    total: int
    category_totals: dict[str, int]
    largest: ExpenseRecord | None


def build_summary(records: list[ExpenseRecord]) -> ExpenseSummary:
    category_totals: dict[str, int] = {}
    largest: ExpenseRecord | None = None
    total = 0

    for record in records:
        total += record.amount
        category_totals[record.category] = category_totals.get(record.category, 0) + record.amount
        if largest is None or record.amount > largest.amount:
            largest = record

    return ExpenseSummary(
        total=total,
        category_totals=category_totals,
        largest=largest,
    )


def top_expenses(records: list[ExpenseRecord], limit: int = 10) -> list[ExpenseRecord]:
    return sorted(records, key=lambda record: record.amount, reverse=True)[:limit]
```

- [ ] **Step 4: Run analysis tests to verify they pass**

Run: `pytest tests/test_analysis.py -v`

Expected: PASS for all 3 tests.

- [ ] **Step 5: Commit**

```bash
git add src/expense_bot/analysis.py tests/test_analysis.py
git commit -m "feat: analyze expenses"
```

## Task 5: Postgres Repository And Schema

**Files:**
- Create: `sql/001_create_expenses.sql`
- Create: `src/expense_bot/repository.py`

- [ ] **Step 1: Create database schema script**

Create `sql/001_create_expenses.sql`:

```sql
CREATE TABLE IF NOT EXISTS expenses (
    id BIGSERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL,
    description TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    category TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    spent_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_spent_at
    ON expenses (telegram_user_id, spent_at DESC);

CREATE INDEX IF NOT EXISTS idx_expenses_user_category
    ON expenses (telegram_user_id, category);
```

- [ ] **Step 2: Implement repository**

Create `src/expense_bot/repository.py`:

```python
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

from expense_bot.models import ExpenseRecord, ParsedExpense


class ExpenseRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def create_expense(
        self,
        telegram_user_id: int,
        parsed: ParsedExpense,
        category: str,
        spent_at: datetime | None = None,
    ) -> ExpenseRecord:
        actual_spent_at = spent_at or datetime.now(timezone.utc)
        with psycopg.connect(self.database_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO expenses (
                        telegram_user_id, description, amount, category, raw_text, spent_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, telegram_user_id, description, amount, category, raw_text, spent_at
                    """,
                    (
                        telegram_user_id,
                        parsed.description,
                        parsed.amount,
                        category,
                        parsed.raw_text,
                        actual_spent_at,
                    ),
                )
                row = cur.fetchone()
        return _row_to_record(row)

    def list_month(self, telegram_user_id: int, year: int, month: int) -> list[ExpenseRecord]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, telegram_user_id, description, amount, category, raw_text, spent_at
                    FROM expenses
                    WHERE telegram_user_id = %s
                      AND spent_at >= make_timestamptz(%s, %s, 1, 0, 0, 0)
                      AND spent_at < make_timestamptz(%s, %s, 1, 0, 0, 0) + INTERVAL '1 month'
                    ORDER BY spent_at DESC, id DESC
                    """,
                    (telegram_user_id, year, month, year, month),
                )
                rows = cur.fetchall()
        return [_row_to_record(row) for row in rows]

    def recent(self, telegram_user_id: int, limit: int = 10) -> list[ExpenseRecord]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, telegram_user_id, description, amount, category, raw_text, spent_at
                    FROM expenses
                    WHERE telegram_user_id = %s
                    ORDER BY spent_at DESC, id DESC
                    LIMIT %s
                    """,
                    (telegram_user_id, limit),
                )
                rows = cur.fetchall()
        return [_row_to_record(row) for row in rows]

    def update_category(self, telegram_user_id: int, expense_id: int, category: str) -> ExpenseRecord | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE expenses
                    SET category = %s, updated_at = NOW()
                    WHERE telegram_user_id = %s AND id = %s
                    RETURNING id, telegram_user_id, description, amount, category, raw_text, spent_at
                    """,
                    (category, telegram_user_id, expense_id),
                )
                row = cur.fetchone()
        return _row_to_record(row) if row else None

    def delete_expense(self, telegram_user_id: int, expense_id: int) -> ExpenseRecord | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM expenses
                    WHERE telegram_user_id = %s AND id = %s
                    RETURNING id, telegram_user_id, description, amount, category, raw_text, spent_at
                    """,
                    (telegram_user_id, expense_id),
                )
                row = cur.fetchone()
        return _row_to_record(row) if row else None


def _row_to_record(row) -> ExpenseRecord:
    return ExpenseRecord(
        id=row["id"],
        telegram_user_id=row["telegram_user_id"],
        description=row["description"],
        amount=row["amount"],
        category=row["category"],
        raw_text=row["raw_text"],
        spent_at=row["spent_at"],
    )
```

- [ ] **Step 3: Run pure unit tests to ensure repository imports do not break the package**

Run: `pytest tests/test_config.py tests/test_parser.py tests/test_categorizer.py tests/test_analysis.py -v`

Expected: PASS for all existing tests.

- [ ] **Step 4: Commit**

```bash
git add sql/001_create_expenses.sql src/expense_bot/repository.py
git commit -m "feat: add postgres repository"
```

## Task 6: Telegram Bot Application

**Files:**
- Create: `src/expense_bot/telegram_app.py`
- Create: `src/expense_bot/__main__.py`
- Modify: `README.md`

- [ ] **Step 1: Implement Telegram app module**

Create `src/expense_bot/telegram_app.py`:

```python
from datetime import date

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from expense_bot.analysis import build_summary, top_expenses
from expense_bot.categorizer import choose_category
from expense_bot.config import Config
from expense_bot.parser import ParseError, parse_expense_message, parse_month_arg
from expense_bot.repository import ExpenseRepository


def build_application(config: Config) -> Application:
    repository = ExpenseRepository(config.database_url)
    application = Application.builder().token(config.telegram_bot_token).build()

    application.bot_data["repository"] = repository

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("summary", summary))
    application.add_handler(CommandHandler("top", top))
    application.add_handler(CommandHandler("recent", recent))
    application.add_handler(CommandHandler("category", category))
    application.add_handler(CommandHandler("edit", edit))
    application.add_handler(CommandHandler("delete_last", delete_last))
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, record_expense))

    return application


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Kirim pengeluaran seperti: makan siang 35000")


async def record_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repository = _repository(context)
    try:
        parsed = parse_expense_message(update.message.text)
        category_name = choose_category(parsed.description, parsed.explicit_category)
        record = repository.create_expense(
            telegram_user_id=update.effective_user.id,
            parsed=parsed,
            category=category_name,
            spent_at=update.message.date,
        )
    except ParseError as exc:
        await update.message.reply_text(str(exc))
        return

    await update.message.reply_text(
        f"Tersimpan #{record.id}: {_rupiah(record.amount)} - {record.description} ({record.category})"
    )


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repository = _repository(context)
    try:
        year, month = parse_month_arg(" ".join(context.args), today=date.today())
    except ParseError as exc:
        await update.message.reply_text(str(exc))
        return

    records = repository.list_month(update.effective_user.id, year, month)
    expense_summary = build_summary(records)
    lines = [f"Summary {year:04d}-{month:02d}", f"Total: {_rupiah(expense_summary.total)}"]

    if expense_summary.category_totals:
        lines.append("Kategori terbesar:")
        for category_name, total in sorted(
            expense_summary.category_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            lines.append(f"- {category_name}: {_rupiah(total)}")

    if expense_summary.largest:
        largest = expense_summary.largest
        lines.append(f"Terbesar: #{largest.id} {_rupiah(largest.amount)} - {largest.description}")

    await update.message.reply_text("\n".join(lines))


async def top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repository = _repository(context)
    try:
        year, month = parse_month_arg(" ".join(context.args), today=date.today())
    except ParseError as exc:
        await update.message.reply_text(str(exc))
        return

    records = top_expenses(repository.list_month(update.effective_user.id, year, month))
    if not records:
        await update.message.reply_text(f"Belum ada pengeluaran untuk {year:04d}-{month:02d}.")
        return

    lines = [f"Top pengeluaran {year:04d}-{month:02d}:"]
    for record in records:
        lines.append(f"#{record.id} {_rupiah(record.amount)} - {record.description} ({record.category})")
    await update.message.reply_text("\n".join(lines))


async def recent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    records = _repository(context).recent(update.effective_user.id)
    if not records:
        await update.message.reply_text("Belum ada pengeluaran.")
        return

    lines = ["Transaksi terbaru:"]
    for record in records:
        lines.append(f"#{record.id} {_rupiah(record.amount)} - {record.description} ({record.category})")
    await update.message.reply_text("\n".join(lines))


async def category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Format: /category transport")
        return

    records = _repository(context).recent(update.effective_user.id, limit=1)
    if not records:
        await update.message.reply_text("Belum ada transaksi untuk dikoreksi.")
        return

    category_name = " ".join(context.args).strip().lower()
    updated = _repository(context).update_category(update.effective_user.id, records[0].id, category_name)
    await update.message.reply_text(
        f"Kategori #{updated.id} diubah: {updated.description} ({updated.category})"
    )


async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 3 or context.args[1].lower() != "kategori":
        await update.message.reply_text("Format: /edit 12 kategori transport")
        return

    try:
        expense_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID transaksi harus angka.")
        return

    category_name = " ".join(context.args[2:]).strip().lower()
    updated = _repository(context).update_category(update.effective_user.id, expense_id, category_name)
    if not updated:
        await update.message.reply_text(f"Transaksi #{expense_id} tidak ditemukan.")
        return

    await update.message.reply_text(
        f"Kategori #{updated.id} diubah: {updated.description} ({updated.category})"
    )


async def delete_last(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    records = _repository(context).recent(update.effective_user.id, limit=1)
    if not records:
        await update.message.reply_text("Belum ada transaksi untuk dihapus.")
        return

    deleted = _repository(context).delete_expense(update.effective_user.id, records[0].id)
    await update.message.reply_text(f"Dihapus #{deleted.id}: {_rupiah(deleted.amount)} - {deleted.description}")


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Format: /delete 12")
        return

    try:
        expense_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID transaksi harus angka.")
        return

    deleted = _repository(context).delete_expense(update.effective_user.id, expense_id)
    if not deleted:
        await update.message.reply_text(f"Transaksi #{expense_id} tidak ditemukan.")
        return

    await update.message.reply_text(f"Dihapus #{deleted.id}: {_rupiah(deleted.amount)} - {deleted.description}")


def _repository(context: ContextTypes.DEFAULT_TYPE) -> ExpenseRepository:
    return context.application.bot_data["repository"]


def _rupiah(amount: int) -> str:
    return f"Rp{amount:,}".replace(",", ".")
```

- [ ] **Step 2: Add entrypoint**

Create `src/expense_bot/__main__.py`:

```python
from expense_bot.config import load_config
from expense_bot.telegram_app import build_application


def main() -> None:
    config = load_config()
    application = build_application(config)
    application.run_polling()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run unit tests**

Run: `pytest -v`

Expected: PASS for all unit tests.

- [ ] **Step 4: Commit**

```bash
git add src/expense_bot/telegram_app.py src/expense_bot/__main__.py README.md
git commit -m "feat: add telegram bot application"
```

## Task 7: Local Secret File And Smoke Check

**Files:**
- Create local only: `.env`
- No commit for `.env`

- [ ] **Step 1: Create `.env` locally**

Create `.env` with the real Telegram token provided by the user and local database URL:

```dotenv
TELEGRAM_BOT_TOKEN=<real-token-from-user>
DATABASE_URL=postgresql://localhost:5432/bot_pengeluaran
```

Do not print the real token in terminal output, commit messages, README, or final response.

- [ ] **Step 2: Confirm `.env` is ignored**

Run: `git status --short --ignored .env`

Expected: output contains `!! .env`.

- [ ] **Step 3: Run all tests**

Run: `pytest -v`

Expected: PASS for all tests.

- [ ] **Step 4: Prepare database manually if needed**

Run these commands only if the local database does not already exist:

```bash
createdb bot_pengeluaran
psql bot_pengeluaran -f sql/001_create_expenses.sql
```

Expected: table `expenses` exists in local Postgres.

- [ ] **Step 5: Start bot locally**

Run: `python -m expense_bot`

Expected: process stays running and Telegram polling starts without a token or database configuration error.

- [ ] **Step 6: Manual Telegram smoke test**

Send these messages to the bot:

```text
makan siang 35000
gojek 18000 transport
kopi 25rb
/recent
/summary
/top
/category food
```

Expected:

- Expense messages reply with `Tersimpan #...`.
- `/recent` lists the saved transactions with IDs.
- `/summary` shows total and category totals.
- `/top` lists largest expenses first.
- `/category food` changes the latest transaction category.

Do not commit `.env`.

## Self-Review

- Spec coverage: free-form input, Postgres storage, local polling, category guessing, corrections, summaries, top expenses, setup docs, and local-only secret handling are all covered by tasks.
- Placeholder scan: no `TBD`, `TODO`, or undefined future implementation steps remain. The only angle-bracket placeholder is `<real-token-from-user>` in the local secret task, intentionally preventing the token from being stored in the plan.
- Type consistency: `ParsedExpense`, `ExpenseRecord`, `Config`, parser functions, categorizer functions, repository methods, and Telegram app calls use consistent names across tasks.
