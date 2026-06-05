from dataclasses import dataclass
from typing import Dict, List, Optional

from expense_bot.models import ExpenseRecord

@dataclass(frozen=True)
class ExpenseSummary:
    total: int
    category_totals: Dict[str, int]
    largest: Optional[ExpenseRecord]

def build_summary(records: List[ExpenseRecord]) -> ExpenseSummary:
    category_totals: Dict[str, int] = {}
    largest: Optional[ExpenseRecord] = None
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

def top_expenses(records: List[ExpenseRecord], limit: int = 10) -> List[ExpenseRecord]:
    return sorted(records, key=lambda record: record.amount, reverse=True)[:limit]
