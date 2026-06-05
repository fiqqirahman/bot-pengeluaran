from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class ParsedExpense:
    description: str
    amount: int
    explicit_category: Optional[str]
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
