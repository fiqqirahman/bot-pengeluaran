import re
from datetime import date
from typing import Optional, Tuple

from expense_bot.models import ParsedExpense

class ParseError(ValueError):
    pass

_AMOUNT_RE = re.compile(r"(?<!\w)(\d+(?:[.,]\d+)?)(rb|k)?(?!\w)", re.IGNORECASE)
_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")

def parse_expense_message(text: str) -> ParsedExpense:
    raw_text = text.strip()
    match = _AMOUNT_RE.search(raw_text)
    if not match:
        raise ParseError("Tidak menemukan nominal. Contoh: makan siang 35000")

    amount = _parse_amount(match.group(1), match.group(2))
    before = raw_text[: match.start()].strip()
    after = raw_text[match.end() :].strip()

    explicit_category = after.lower() if after else None
    description = before
    if not description:
        raise ParseError("Deskripsi pengeluaran tidak boleh kosong.")

    return ParsedExpense(
        description=description,
        amount=amount,
        explicit_category=explicit_category,
        raw_text=raw_text,
    )

def parse_month_arg(arg: str, today: Optional[date] = None) -> Tuple[int, int]:
    clean_arg = arg.strip()
    if not clean_arg:
        current = today or date.today()
        return current.year, current.month

    match = _MONTH_RE.match(clean_arg)
    if not match:
        raise ParseError("Format bulan harus YYYY-MM, contoh: 2026-05")

    year = int(match.group(1))
    month = int(match.group(2))
    if month < 1 or month > 12:
        raise ParseError("Format bulan harus YYYY-MM, contoh: 2026-05")

    return year, month

def _parse_amount(number_text: str, suffix: Optional[str]) -> int:
    normalized = number_text.replace(",", ".")
    value = float(normalized)
    if suffix and suffix.lower() in {"rb", "k"}:
        value *= 1000
    return int(value)
