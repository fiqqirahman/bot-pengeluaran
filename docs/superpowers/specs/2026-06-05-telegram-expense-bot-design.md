# Telegram Expense Bot Design

## Goal

Build a local-only Telegram bot for recording personal expenses quickly from free-form chat messages, storing them in a local Postgres database, and returning useful spending analysis through Telegram commands.

The bot will run on the user's laptop. It will not require deployment to a server and will not be pushed to any remote repository.

## Scope

The first version will support:

- Recording expenses from short free-form messages.
- Parsing amounts written as plain numbers or Indonesian shorthand, such as `35000`, `25rb`, and `25k`.
- Optional explicit categories in the message.
- Automatic category guessing when no category is provided.
- Correcting the latest transaction quickly.
- Correcting or deleting older transactions by ID.
- Monthly summaries and largest-expense analysis.

Out of scope for the first version:

- Multi-currency support.
- Receipt image OCR.
- Bank import.
- Web dashboard.
- Cloud hosting.
- Remote repository setup.

## User Input

The primary input style is a normal Telegram message:

```text
makan siang 35000
gojek 18000 transport
kopi 25rb
```

Parsing rules:

- The bot identifies one amount from the message.
- Text before and around the amount becomes the description.
- A recognized trailing category can be treated as the explicit category.
- If no category is explicit, the bot guesses one from keywords.
- The original message is stored as `raw_text` for auditability.

If the bot cannot find a valid amount, it replies with a short error and example format.

## Telegram Commands

The bot will support these commands:

- `/summary`: Show the current month summary.
- `/summary YYYY-MM`: Show a specific month summary, for example `/summary 2026-05`.
- `/top`: Show the 10 largest expenses in the current month.
- `/top YYYY-MM`: Show the 10 largest expenses in a specific month.
- `/recent`: Show recent transactions with IDs.
- `/category <category>`: Change the category of the latest transaction.
- `/edit <id> kategori <category>`: Change the category of a transaction by ID.
- `/delete_last`: Delete the latest transaction for the current Telegram user.
- `/delete <id>`: Delete a transaction by ID.

The command names intentionally stay small and memorable. More detailed editing can be added later if the first version proves useful.

## Category Behavior

The bot uses a hybrid approach:

- If the message includes an explicit category, that category wins.
- If not, the bot guesses from keyword rules.
- If no rule matches, the category becomes `uncategorized`.
- The user can correct the latest transaction with `/category <category>`.
- The user can correct an older transaction with `/edit <id> kategori <category>`.

Initial keyword rules:

- `food`: `makan`, `kopi`, `ayam`, `nasi`, `resto`, `bakso`, `mie`, `minum`.
- `transport`: `gojek`, `grab`, `taxi`, `bensin`, `parkir`, `tol`.
- `utilities`: `token`, `listrik`, `internet`, `pulsa`, `air`.
- `shopping`: `beli`, `tokopedia`, `shopee`, `laundry`.
- `health`: `obat`, `dokter`, `apotek`, `vitamin`.

These rules will live in one small module so they are easy to change.

## Data Model

The first version uses a single Postgres table named `expenses`.

Columns:

- `id`: Primary key.
- `telegram_user_id`: Telegram user ID, used to separate records if more than one user ever talks to the bot.
- `description`: Parsed expense description.
- `amount`: Expense amount in Indonesian rupiah as an integer.
- `category`: Final category.
- `raw_text`: Original Telegram message.
- `spent_at`: Timestamp for when the expense happened. In version one, this defaults to the message time.
- `created_at`: Insert timestamp.
- `updated_at`: Last update timestamp.

This single-table model is enough for the first version and keeps analysis queries simple.

## Architecture

Use a small Python application with these responsibilities:

- Telegram adapter: receives messages and routes commands.
- Parser: turns free-form text into structured expense data.
- Categorizer: applies keyword-based category rules.
- Repository: reads and writes Postgres records.
- Analysis service: calculates summaries and top expenses.
- Configuration: loads Telegram token and database URL from environment variables.

Recommended libraries:

- `python-telegram-bot` for Telegram polling.
- `psycopg` for Postgres access.
- `python-dotenv` for local `.env` loading.
- `pytest` for tests.

The bot will use Telegram polling so the laptop does not need a public webhook URL.

## Data Flow

Recording an expense:

1. Telegram message arrives.
2. Bot ignores commands and parses regular text as an expense.
3. Parser extracts amount and description.
4. Categorizer chooses explicit, guessed, or `uncategorized` category.
5. Repository inserts the record into Postgres.
6. Bot replies with saved amount, category, and transaction ID.

Running analysis:

1. User sends `/summary`, `/summary YYYY-MM`, `/top`, or `/top YYYY-MM`.
2. Bot resolves the requested month.
3. Repository queries matching rows for that user and month.
4. Analysis service computes totals, category totals, and largest transactions.
5. Bot returns a concise text summary.

Correcting data:

1. User sends `/category <category>`, `/edit <id> kategori <category>`, `/delete_last`, or `/delete <id>`.
2. Bot scopes the operation to the Telegram user.
3. Repository updates or deletes the matching row.
4. Bot replies with the updated or deleted transaction details.

## Error Handling

Expected errors should return short, helpful Telegram replies:

- Missing or invalid amount.
- Invalid month format.
- Transaction ID not found.
- Empty category.
- Database connection failure.

The bot should log internal errors locally while avoiding long stack traces in Telegram replies.

## Testing Strategy

Tests should focus on the highest-risk behavior:

- Amount parsing: `35000`, `25rb`, `25k`, and invalid text.
- Description and category parsing.
- Category guessing rules.
- Month filter parsing.
- Analysis calculations for total, category totals, and top expenses.

Database integration can be covered lightly after the core parser and analysis behavior are stable.

## Local Operation

The project should include:

- `.env.example` documenting required environment variables.
- A README with local setup steps.
- A database initialization script or migration file.
- A command to run the bot locally.
- A test command.

No remote repository or deployment step is required.
