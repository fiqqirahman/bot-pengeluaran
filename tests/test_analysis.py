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
        spent_at=datetime(2026, 6, id, 12, 0, 0)
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
