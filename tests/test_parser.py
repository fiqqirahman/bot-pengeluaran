from datetime import date

import pytest

from expense_bot.parser import ParseError, parse_expense_message, parse_month_arg

def test_parse_plain_number_expense_without_category():
    parsed = parse_expense_message("makan siang 35000")
    assert parsed.description == "makan siang"
    assert parsed.amount == 35000
    assert parsed.explicit_category is None

def test_parse_expense_with_trailing_category():
    parsed = parse_expense_message("gojek 18000 transport")
    assert parsed.description == "gojek"
    assert parsed.amount == 18000
    assert parsed.explicit_category == "transport"

def test_parse_indonesian_rb_amount():
    parsed = parse_expense_message("kopi 25rb")
    assert parsed.amount == 25000

def test_parse_k_amount():
    parsed = parse_expense_message("kopi 25k")
    assert parsed.amount == 25000

def test_parse_rejects_text_without_amount():
    with pytest.raises(ParseError, match="nominal"):
        parse_expense_message("makan siang")

def test_parse_number_with_dot_separator():
    parsed = parse_expense_message("gojek 25.000")
    assert parsed.amount == 25000

def test_parse_rejects_comma_separator():
    with pytest.raises(ParseError, match="tidak valid"):
        parse_expense_message("gojek 25,000")

def test_parse_decimal_with_suffix():
    parsed = parse_expense_message("kopi 2.5k")
    assert parsed.amount == 2500

def test_parse_number_with_multiple_separators():
    parsed = parse_expense_message("laptop 1.500.000")
    assert parsed.amount == 1500000
