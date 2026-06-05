# AGENTS.md - AI Agent Guidance

## Project Overview

Local Telegram bot for recording personal expenses in Indonesian Rupiah. Stores data in local PostgreSQL. Runs on user's laptop via Telegram polling.

## Documentation Index

Before making any changes, READ the relevant documentation:

| Document | When to Read |
|----------|--------------|
| `docs/architecture.md` | Understanding project structure, modules, data flow |
| `docs/features.md` | Knowing what features exist, are planned, or out of scope |
| `docs/database.md` | Working with expenses table, queries, schema |
| `docs/api.md` | Understanding Telegram commands and user interaction |

## Current Status

**Implemented:**
- `src/expense_bot/config.py` - Environment config loading
- `tests/test_config.py` - Config tests

**Planned (see docs for specs):**
- `src/expense_bot/models.py` - Dataclasses
- `src/expense_bot/parser.py` - Free-form text parsing
- `src/expense_bot/categorizer.py` - Category guessing
- `src/expense_bot/analysis.py` - Summary calculations
- `src/expense_bot/repository.py` - Postgres CRUD
- `src/expense_bot/telegram_app.py` - Telegram handlers
- `src/expense_bot/__main__.py` - Entrypoint
- `sql/001_create_expenses.sql` - Database migration

## Code Style

- Python 3.9+ compatible
- Type hints on all function signatures
- Docstrings on public functions
- Frozen dataclasses for immutable data
- Pure functions where possible (testable without DB/Telegram)
- Tests with pytest, monkeypatch for env vars

## Conventions

### Naming
- Modules: `snake_case.py`
- Functions: `snake_case()`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Test files: `test_<module>.py`

### Project Layout
```
src/expense_bot/    # Main package
tests/              # Test files (mirror src structure)
docs/               # Documentation
sql/                # Database migrations
```

### Dependencies
- `python-telegram-bot>=21.0` - Telegram API
- `psycopg[binary]>=3.2.0` - PostgreSQL driver
- `python-dotenv>=1.0.1` - Env loading
- `pytest>=8.0.0` - Testing (dev dependency)

## Key Design Decisions

1. **Polling, not webhook** - Runs locally, no public URL needed
2. **Single table** - `expenses` table for all expense data
3. **User-scoped** - All queries filter by `telegram_user_id`
4. **Pure logic separated** - Parser/categorizer/analysis are independent of Telegram/DB
5. **Frozen dataclasses** - Prevent accidental mutation
6. **Indonesian amounts** - Support `25rb`, `25k` formats

## When Implementing

### For New Features
1. Check `docs/features.md` for specifications
2. Check `docs/api.md` for user-facing behavior
3. Check `docs/database.md` for data model needs
4. Write tests first (TDD approach)
5. Implement the module
6. Run `pytest` to verify

### For Database Changes
1. Read `docs/database.md` for schema
2. Create migration in `sql/` folder
3. Update `docs/database.md` if schema changes
4. Test queries manually if possible

### For Telegram Commands
1. Read `docs/api.md` for command specs
2. Implement handler in `telegram_app.py`
3. Follow error response patterns
4. Keep responses in Indonesian

## Testing

- **Unit tests**: Parser, categorizer, analysis (no external deps)
- **Integration tests**: Repository (may need test DB)
- **Test command**: `pytest` or `pytest -v`
- **Test location**: `tests/` directory, mirror `src/` structure

## Common Tasks

### Add a new category keyword
- Edit: `src/expense_bot/categorizer.py`
- Test: `tests/test_categorizer.py`
- Update: `docs/features.md` keyword table

### Add a new Telegram command
- Edit: `src/expense_bot/telegram_app.py`
- Document: `docs/api.md`
- Follow existing command pattern

### Change database schema
- Create: `sql/002_<description>.sql`
- Update: `docs/database.md`
- Update: `src/expense_bot/repository.py`

## Environment Variables

Required in `.env`:
```
TELEGRAM_BOT_TOKEN=<your-bot-token>
DATABASE_URL=postgresql://localhost:5432/bot_pengeluaran
```

## Running the Bot

```bash
# Setup
pip install -e ".[dev]"

# Create database
createdb bot_pengeluaran
psql bot_pengeluaran -f sql/001_create_expenses.sql

# Run tests
pytest

# Start bot
python -m expense_bot
```

## Important Notes

- **No remote deployment** - Bot runs locally on user's laptop
- **No cloud services** - All data stays local
- **Indonesian user** - Responses in Indonesian
- **Personal use** - Single user or few users, not production scale
- **Raw text stored** - Original message preserved for audit
