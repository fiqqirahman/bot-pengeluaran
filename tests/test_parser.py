from datetime import date

import pytest

from expense_bot.parser import ParseError, parse_expense_message, parse_month_arg

def test_parse_plain_number_expense_without_category():
    parsed = parse_expense_message("makan siang 35000")

    assert parsed.description == "makan siang"
    assert parsed.amount == 35000
    assert parsed.explicit_category is None
    assert parsed.raw_text == "makan siang 35000"

def test_parse_expense_with_trailing_category():
    parsed = parse_expense_message("gojek 18000 transport")

    assert parsed.description == "gojek"
    assert parsed.amount == 18000
    assert parsed.explicit_category == "transport"

def test_parse_indonesian_rb_amount():
    parsed = parse_expense_message("kopi 25rb")

    assert parsed.description == "kopi"
    assert parsed.amount == 25000
    assert parsed.explicit_category is None

def test_parse_k_amount():
    parsed = parse_expense_message("kopi 25k")

    assert parsed.description == "kopi"
    assert parsed.amount == 25000

def test_parse_rejects_text_without_amount():
    with pytest.raises(ParseError, match="nominal"):
        parse_expense_message("makan siang")

def test_parse_current_month_when_arg_empty():
    assert parse_month_arg("", today=date(2026, 6, 5)) == (2026, 6)

def test_parse_specific_month():
    assert parse_month_arg("2026-05", today=date(2026, 6, 5)) == (2026, 5)

def test_parse_rejects_invalid_month():
    with pytest.raises(ParseError, match="YYYY-MM"):
        parse_month_arg("mei", today=date(2026, 6, 5))
