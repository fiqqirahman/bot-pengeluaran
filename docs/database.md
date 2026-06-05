# Database

## Data Model

Single table `expenses` in PostgreSQL.

### Columns

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | SERIAL | auto-increment | Primary key |
| `telegram_user_id` | BIGINT | - | Telegram user ID, scopes all queries |
| `description` | VARCHAR(500) | - | Parsed expense description |
| `amount` | INTEGER | - | Amount in Indonesian Rupiah (no decimals) |
| `category` | VARCHAR(50) | - | Final category (explicit, guessed, or `uncategorized`) |
| `raw_text` | TEXT | - | Original Telegram message for audit |
| `spent_at` | TIMESTAMP | message time | When the expense happened (v1: message timestamp) |
| `created_at` | TIMESTAMP | NOW() | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOW() | Last update timestamp |

### Constraints

- `amount` must be positive integer (> 0)
- `category` must not be empty
- `telegram_user_id` is NOT a foreign key (no user table in v1)

### Indexes

```sql
CREATE INDEX idx_expenses_user_month 
ON expenses (telegram_user_id, spent_at);
```

This index supports the two most common queries:
- Get all expenses for a user in a specific month
- Get latest expense for a user

## SQL Migration

### 001_create_expenses.sql

```sql
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL,
    description VARCHAR(500) NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    category VARCHAR(50) NOT NULL,
    raw_text TEXT NOT NULL,
    spent_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_expenses_user_month 
ON expenses (telegram_user_id, spent_at);
```

## Query Patterns

### Insert Expense
```sql
INSERT INTO expenses (telegram_user_id, description, amount, category, raw_text, spent_at)
VALUES (%s, %s, %s, %s, %s, NOW())
RETURNING *;
```

### Get Expenses by Month
```sql
SELECT * FROM expenses
WHERE telegram_user_id = %s 
AND DATE_TRUNC('month', spent_at) = DATE_TRUNC('month', %s::date)
ORDER BY spent_at DESC;
```

### Get Top N Expenses by Month
```sql
SELECT * FROM expenses
WHERE telegram_user_id = %s 
AND DATE_TRUNC('month', spent_at) = DATE_TRUNC('month', %s::date)
ORDER BY amount DESC
LIMIT %s;
```

### Get Latest Expense for User
```sql
SELECT * FROM expenses
WHERE telegram_user_id = %s
ORDER BY spent_at DESC
LIMIT 1;
```

### Update Category by ID
```sql
UPDATE expenses 
SET category = %s, updated_at = NOW()
WHERE id = %s AND telegram_user_id = %s
RETURNING *;
```

### Delete by ID
```sql
DELETE FROM expenses 
WHERE id = %s AND telegram_user_id = %s
RETURNING *;
```

### Monthly Summary Aggregation
```sql
SELECT 
    category,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount
FROM expenses
WHERE telegram_user_id = %s 
AND DATE_TRUNC('month', spent_at) = DATE_TRUNC('month', %s::date)
GROUP BY category
ORDER BY total_amount DESC;
```

### Grand Total for Month
```sql
SELECT SUM(amount) as grand_total
FROM expenses
WHERE telegram_user_id = %s 
AND DATE_TRUNC('month', spent_at) = DATE_TRUNC('month', %s::date);
```

## Data Integrity Rules

1. **User Scoping**: Every query MUST filter by `telegram_user_id`
2. **Amount Validation**: Amount must be > 0 (enforced by CHECK constraint)
3. **Category Required**: Category must not be empty string
4. **Single User Isolation**: Users cannot see or modify other users' expenses
5. **Audit Trail**: `raw_text` preserves original input; `created_at`/`updated_at` track changes

## Local Setup

```bash
# Create database
createdb bot_pengeluaran

# Run migration
psql bot_pengeluaran -f sql/001_create_expenses.sql

# Verify table exists
psql bot_pengeluaran -c "\d expenses"
```

## Sample Data

```sql
-- For testing
INSERT INTO expenses (telegram_user_id, description, amount, category, raw_text, spent_at)
VALUES 
    (12345678, 'makan siang', 35000, 'food', 'makan siang 35000', NOW()),
    (12345678, 'gojek', 18000, 'transport', 'gojek 18000 transport', NOW()),
    (12345678, 'kopi', 25000, 'food', 'kopi 25rb', NOW());
```
