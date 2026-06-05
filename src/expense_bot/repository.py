import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from expense_bot.models import ExpenseRecord, ParsedExpense

class ExpenseRepository:
    def __init__(self, database_url: str):
        # We assume database_url is something like "sqlite:///bot_pengeluaran.db"
        # We strip "sqlite:///" to get the path
        if database_url.startswith("sqlite:///"):
            self.db_path = database_url[10:]
        else:
            self.db_path = database_url

        self._init_db()

    def _init_db(self):
        with open("sql/001_create_expenses.sql", "r") as f:
            script = f.read()
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(script)

    def create_expense(
        self,
        telegram_user_id: int,
        parsed: ParsedExpense,
        category: str,
        spent_at: Optional[datetime] = None,
    ) -> ExpenseRecord:
        actual_spent_at = spent_at or datetime.now(timezone.utc)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Format datetime to string for sqlite
            spent_at_str = actual_spent_at.isoformat()
            
            cursor.execute(
                """
                INSERT INTO expenses (
                    telegram_user_id, description, amount, category, raw_text, spent_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    telegram_user_id,
                    parsed.description,
                    parsed.amount,
                    category,
                    parsed.raw_text,
                    spent_at_str,
                ),
            )
            
            expense_id = cursor.lastrowid
            cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
            row = cursor.fetchone()
            
        return _row_to_record(row)

    def list_month(self, telegram_user_id: int, year: int, month: int) -> List[ExpenseRecord]:
        start_date = f"{year}-{month:02d}-01T00:00:00"
        
        # Calculate next month for the upper bound
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        end_date = f"{next_year}-{next_month:02d}-01T00:00:00"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT *
                FROM expenses
                WHERE telegram_user_id = ?
                  AND spent_at >= ?
                  AND spent_at < ?
                ORDER BY spent_at DESC, id DESC
                """,
                (telegram_user_id, start_date, end_date),
            )
            rows = cursor.fetchall()
            
        return [_row_to_record(row) for row in rows]

    def recent(self, telegram_user_id: int, limit: int = 10) -> List[ExpenseRecord]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT *
                FROM expenses
                WHERE telegram_user_id = ?
                ORDER BY spent_at DESC, id DESC
                LIMIT ?
                """,
                (telegram_user_id, limit),
            )
            rows = cursor.fetchall()
            
        return [_row_to_record(row) for row in rows]

    def update_category(self, telegram_user_id: int, expense_id: int, category: str) -> Optional[ExpenseRecord]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE expenses
                SET category = ?, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_user_id = ? AND id = ?
                """,
                (category, telegram_user_id, expense_id),
            )
            
            if cursor.rowcount == 0:
                return None
                
            cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
            row = cursor.fetchone()
            
        return _row_to_record(row)

    def delete_expense(self, telegram_user_id: int, expense_id: int) -> Optional[ExpenseRecord]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM expenses WHERE telegram_user_id = ? AND id = ?", (telegram_user_id, expense_id))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            cursor.execute(
                "DELETE FROM expenses WHERE telegram_user_id = ? AND id = ?",
                (telegram_user_id, expense_id),
            )
            
        return _row_to_record(row)

def _row_to_record(row) -> ExpenseRecord:
    # Handle parsing ISO datetime strings back to datetime objects
    spent_at = row["spent_at"]
    if isinstance(spent_at, str):
        try:
            spent_at = datetime.fromisoformat(spent_at)
        except ValueError:
            spent_at = datetime.strptime(spent_at, "%Y-%m-%d %H:%M:%S")

    return ExpenseRecord(
        id=row["id"],
        telegram_user_id=row["telegram_user_id"],
        description=row["description"],
        amount=row["amount"],
        category=row["category"],
        raw_text=row["raw_text"],
        spent_at=spent_at,
    )
