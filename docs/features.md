# Features

## Current Implementation Status

| Feature | Status | Module | Tests |
|---------|--------|--------|-------|
| Environment config loading | ✅ | config.py | test_config.py |
| Free-form expense parsing | 📋 | parser.py | test_parser.py |
| Category guessing | 📋 | categorizer.py | test_categorizer.py |
| Database operations | 📋 | repository.py | - |
| Monthly summaries | 📋 | analysis.py | test_analysis.py |
| Top expenses | 📋 | analysis.py | test_analysis.py |
| Telegram bot handlers | 📋 | telegram_app.py | - |

✅ = Implemented | 📋 = Planned

## Feature Details

### 1. Free-Form Expense Recording ✅ Spec / 📋 Implementation

**User Experience:**
```
User: makan siang 35000
Bot: Tersimpan #1: Rp35.000 - makan siang (food)

User: gojek 18000 transport
Bot: Tersimpan #2: Rp18.000 - gojek (transport)

User: kopi 25rb
Bot: Tersimpan #3: Rp25.000 - kopi (food)
```

**Parsing Rules:**
- Extract one amount from the message (first valid number found)
- Support formats: `35000`, `25rb` (Indonesian "ribu"), `25k`
- Text around the amount becomes the description
- Trailing recognized category becomes explicit category
- If no explicit category, guess from keywords
- Store original message as `raw_text` for auditability

**Error Handling:**
- No valid amount found → "Format: [deskripsi] [jumlah] [kategori]"
- Invalid characters → Skip and continue parsing
- Amount must be positive integer

### 2. Category Guessing 📋

**Behavior:**
- Hybrid approach: explicit category beats guessed category
- If no explicit category, scan description for keywords
- If no keyword match, assign `"uncategorized"`

**Initial Keyword Rules:**
```python
{
    "food": ["makan", "kopi", "ayam", "nasi", "resto", "bakso", "mie", "minum"],
    "transport": ["gojek", "grab", "taxi", "bensin", "parkir", "tol"],
    "utilities": ["token", "listrik", "internet", "pulsa", "air"],
    "shopping": ["beli", "tokopedia", "shopee", "laundry"],
    "health": ["obat", "dokter", "apotek", "vitamin"],
}
```

**Extension:**
- Keywords live in `categorizer.py` for easy updates
- Future: user-defined categories and keywords

### 3. Monthly Summary 📋

**Command:** `/summary` or `/summary YYYY-MM`

**Behavior:**
- No argument → current month (based on server time)
- With argument → parse as `YYYY-MM` format
- Query all expenses for the user in that month
- Calculate total and per-category totals

**Output Format:**
```
📊 Summary Juni 2026

Total: Rp850.000

Kategori:
• food: Rp350.000 (41%)
• transport: Rp180.000 (21%)
• shopping: Rp150.000 (18%)
• utilities: Rp100.000 (12%)
• uncategorized: Rp70.000 (8%)

Transaksi: 24
```

### 4. Top Expenses 📋

**Command:** `/top` or `/top YYYY-MM`

**Behavior:**
- No argument → current month
- With argument → parse as `YYYY-MM` format
- Return 10 largest expenses for that month
- Ordered by amount descending

**Output Format:**
```
🔝 Top 10 - Juni 2026

1. #45: Rp150.000 - belanja bulanan (shopping)
2. #38: Rp100.000 - token listrik (utilities)
3. #52: Rp85.000 - makan malam (food)
4. #41: Rp75.000 - gojek (transport)
5. #49: Rp60.000 - kopi (food)
...
```

### 5. Recent Transactions 📋

**Command:** `/recent`

**Behavior:**
- Show last 10 transactions for the user
- Include transaction ID for editing/deleting
- Most recent first

**Output Format:**
```
📝 Transaksi Terakhir

#52: Rp35.000 - makan siang (food) - 5 Jun 14:30
#51: Rp18.000 - gojek (transport) - 5 Jun 12:15
#50: Rp25.000 - kopi (food) - 5 Jun 10:00
...
```

### 6. Category Correction 📋

**Command:** `/category <category>`

**Behavior:**
- Changes category of the LATEST transaction for this user
- Validates category is not empty
- Updates `updated_at` timestamp

**Example:**
```
User: /category transport
Bot: Kategori #52 diubah: makan siang (transport)
```

### 7. Transaction Edit by ID 📋

**Command:** `/edit <id> kategori <category>`

**Behavior:**
- Changes category of specific transaction by ID
- Scoped to user (cannot edit other users' transactions)
- Returns error if transaction not found

**Example:**
```
User: /edit 45 kategori food
Bot: Kategori #45 diubah: belanja bulanan (food)
```

### 8. Delete Latest Transaction 📋

**Command:** `/delete_last`

**Behavior:**
- Deletes the LATEST transaction for this user
- Returns error if no transactions exist
- Shows deleted transaction details

**Example:**
```
User: /delete_last
Bot: Dihapus #52: Rp35.000 - makan siang
```

### 9. Delete Transaction by ID 📋

**Command:** `/delete <id>`

**Behavior:**
- Deletes specific transaction by ID
- Scoped to user
- Returns error if transaction not found

**Example:**
```
User: /delete 45
Bot: Dihapus #45: Rp150.000 - belanja bulanan
```

## Out of Scope (v1)

These features are NOT included in the first version:

- Multi-currency support
- Receipt image OCR
- Bank statement import
- Web dashboard
- Remote deployment/hosting
- Shared expenses between users
- Budget limits and alerts
- Recurring expenses
- Export to CSV/Excel
- Custom categories per user
- Income tracking

## Future Enhancements (v2+)

Potential additions after v1 is stable:

- `/export` - Export month data to CSV
- `/budget` - Set category budgets
- `/stats` - Advanced analytics
- User-defined categories
- Edit description and amount (not just category)
- Date correction for backdated expenses
- Search by description or category
- Bulk delete/edit operations
