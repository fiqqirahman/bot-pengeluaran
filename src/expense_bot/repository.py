from datetime import datetime, timezone
from typing import List, Optional

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
        spent_at: Optional[datetime] = None,
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

    def list_month(self, telegram_user_id: int, year: int, month: int) -> List[ExpenseRecord]:
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

    def recent(self, telegram_user_id: int, limit: int = 10) -> List[ExpenseRecord]:
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

    def update_category(self, telegram_user_id: int, expense_id: int, category: str) -> Optional[ExpenseRecord]:
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

    def delete_expense(self, telegram_user_id: int, expense_id: int) -> Optional[ExpenseRecord]:
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
