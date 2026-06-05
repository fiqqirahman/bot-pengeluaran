from expense_bot.categorizer import choose_category, guess_category

def test_explicit_category_wins():
    assert choose_category("gojek", "custom") == "custom"

def test_guess_food_category_from_keywords():
    assert guess_category("kopi susu") == "food"

def test_guess_transport_category_from_keywords():
    assert guess_category("gojek ke kantor") == "transport"

def test_guess_uncategorized_when_no_keyword_matches():
    assert guess_category("iuran random") == "uncategorized"
