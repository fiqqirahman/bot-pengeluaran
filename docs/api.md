# API - Telegram Commands & User Interaction

## Message Types

The bot handles two types of user input:
1. **Commands** - Start with `/` (e.g., `/summary`, `/delete 5`)
2. **Free-form messages** - Everything else (e.g., "makan siang 35000")

## Free-Form Expense Messages

### Format
```
[deskripsi] [jumlah] [kategori opsional]
```

### Examples
```
makan siang 35000
→ Description: "makan siang", Amount: 35000, Category: guessed as "food"

gojek 18000 transport
→ Description: "gojek", Amount: 18000, Category: explicit "transport"

kopi 25rb
→ Description: "kopi", Amount: 25000, Category: guessed as "food"

token listrik 50k utilities
→ Description: "token listrik", Amount: 50000, Category: explicit "utilities"
```

### Amount Parsing Rules

| Format | Example | Parsed As |
|--------|---------|-----------|
| Plain number | `35000` | 35000 |
| Indonesian "ribu" | `25rb` | 25000 |
| Thousand shorthand | `25k` | 25000 |
| With dots/commas | `35.000` | 35000 |

### Response Format
```
Tersimpan #<id>: Rp<amount> - <description> (<category>)
```

Example:
```
Tersimpan #1: Rp35.000 - makan siang (food)
```

### Error Responses
```
Format: [deskripsi] [jumlah] [kategori]
Contoh: makan siang 35000 atau gojek 18rb transport
```

## Commands

### /summary

Show monthly spending summary.

**Format:**
```
/summary              # Current month
/summary YYYY-MM      # Specific month
```

**Examples:**
```
/summary
/summary 2026-06
/summary 2025-12
```

**Response:**
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

**Errors:**
- Invalid month format → "Format: /summary YYYY-MM"
- No transactions → "Belum ada transaksi di bulan ini"

---

### /top

Show top 10 largest expenses.

**Format:**
```
/top              # Current month
/top YYYY-MM      # Specific month
```

**Examples:**
```
/top
/top 2026-06
/top 2025-12
```

**Response:**
```
🔝 Top 10 - Juni 2026

1. #45: Rp150.000 - belanja bulanan (shopping)
2. #38: Rp100.000 - token listrik (utilities)
3. #52: Rp85.000 - makan malam (food)
4. #41: Rp75.000 - gojek (transport)
5. #49: Rp60.000 - kopi (food)
6. #47: Rp55.000 - bensin (transport)
7. #50: Rp50.000 - laundry (shopping)
8. #43: Rp45.000 - obat (health)
9. #46: Rp40.000 - parkir (transport)
10. #48: Rp35.000 - makan siang (food)
```

**Errors:**
- Invalid month format → "Format: /top YYYY-MM"
- No transactions → "Belum ada transaksi di bulan ini"

---

### /recent

Show last 10 transactions with IDs.

**Format:**
```
/recent
```

**Response:**
```
📝 Transaksi Terakhir

#52: Rp35.000 - makan siang (food) - 5 Jun 14:30
#51: Rp18.000 - gojek (transport) - 5 Jun 12:15
#50: Rp25.000 - kopi (food) - 5 Jun 10:00
#49: Rp60.000 - bensin (transport) - 4 Jun 18:45
#48: Rp15.000 - parkir (transport) - 4 Jun 18:30
#47: Rp55.000 - makan malam (food) - 4 Jun 19:00
#46: Rp40.000 - token (utilities) - 3 Jun 08:00
#45: Rp150.000 - belanja (shopping) - 2 Jun 16:20
#44: Rp25.000 - kopi (food) - 2 Jun 10:00
#43: Rp45.000 - obat (health) - 1 Jun 12:30
```

**Errors:**
- No transactions → "Belum ada transaksi"

---

### /category

Change category of the LATEST transaction.

**Format:**
```
/category <category_name>
```

**Examples:**
```
/category food
/category transport
/category utilities
```

**Response:**
```
Kategori #52 diubah: makan siang (food)
```

**Errors:**
- Missing category → "Format: /category <kategori>"
- No transactions → "Belum ada transaksi untuk diubah"

---

### /edit

Change category of specific transaction by ID.

**Format:**
```
/edit <id> kategori <category_name>
```

**Examples:**
```
/edit 45 kategori food
/edit 38 kategori transport
```

**Response:**
```
Kategori #45 diubah: belanja bulanan (food)
```

**Errors:**
- Invalid format → "Format: /edit <id> kategori <kategori>"
- Invalid ID → "ID transaksi harus angka"
- Not found → "Transaksi #45 tidak ditemukan"

---

### /delete_last

Delete the LATEST transaction.

**Format:**
```
/delete_last
```

**Response:**
```
Dihapus #52: Rp35.000 - makan siang
```

**Errors:**
- No transactions → "Belum ada transaksi untuk dihapus"

---

### /delete

Delete specific transaction by ID.

**Format:**
```
/delete <id>
```

**Examples:**
```
/delete 45
/delete 38
```

**Response:**
```
Dihapus #45: Rp150.000 - belanja bulanan
```

**Errors:**
- Missing ID → "Format: /delete <id>"
- Invalid ID → "ID transaksi harus angka"
- Not found → "Transaksi #45 tidak ditemukan"

---

## User Isolation

All commands and operations are scoped to the Telegram user:
- Users can only see their own expenses
- Users can only edit/delete their own expenses
- Transaction IDs are unique across all users, but access is restricted by `telegram_user_id`

## Error Handling Strategy

1. **Validation errors** → Short, helpful message with example
2. **Not found errors** → Clear message with the ID/parameter that failed
3. **Database errors** → Generic "Terjadi kesalahan" (don't expose internals)
4. **Internal errors** → Logged locally, not sent to user

## Localization

All user-facing messages are in **Indonesian**:
- Commands can be English (Telegram convention)
- Responses, errors, and summaries are Indonesian
- Category names are English (for simplicity in v1)
