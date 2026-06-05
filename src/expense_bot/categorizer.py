from typing import Optional

CATEGORY_KEYWORDS = {
    "food": ["makan", "kopi", "ayam", "nasi", "resto", "bakso", "mie", "minum"],
    "transport": ["gojek", "grab", "taxi", "bensin", "parkir", "tol"],
    "utilities": ["token", "listrik", "internet", "pulsa", "air"],
    "shopping": ["beli", "tokopedia", "shopee", "laundry"],
    "health": ["obat", "dokter", "apotek", "vitamin"],
}

def choose_category(description: str, explicit_category: Optional[str]) -> str:
    if explicit_category:
        return explicit_category.strip().lower()
    return guess_category(description)

def guess_category(description: str) -> str:
    normalized = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    return "uncategorized"
