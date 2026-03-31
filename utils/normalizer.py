import re
from datetime import date

MONTH_FR = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
}


def normalize_amount(text: str | None) -> tuple[float | None, float | None]:
    """
    Parse French amount strings into (min, max) float tuple (in euros).

    Examples:
        "2 000 000 €"       → (2000000.0, 2000000.0)
        "jusqu'à 2M€"       → (None, 2000000.0)
        "200 000 € à 500 000 €" → (200000.0, 500000.0)
        "300K€"             → (300000.0, 300000.0)
    """
    if not text:
        return None, None

    text = text.lower().strip()

    # Strip common prefixes
    is_max_only = bool(re.search(r"jusqu['\u2019]?[aà]|maximum|max\b|jusqu", text))

    # Extract all numeric values
    amounts = []
    for match in re.finditer(r"[\d\s]+(?:[.,]\d+)?", text):
        raw = match.group().replace(" ", "").replace(",", ".")
        if not raw:
            continue
        try:
            amounts.append(float(raw))
        except ValueError:
            pass

    # Apply multipliers (M = million, K = thousand)
    multiplied = []
    for match in re.finditer(r"([\d\s.,]+)\s*(m|k)€?", text):
        raw = match.group(1).replace(" ", "").replace(",", ".")
        multiplier = {"m": 1_000_000, "k": 1_000}[match.group(2)]
        try:
            multiplied.append(float(raw) * multiplier)
        except ValueError:
            pass

    values = multiplied if multiplied else amounts
    if not values:
        return None, None

    if is_max_only:
        return None, max(values)
    if len(values) == 1:
        return values[0], values[0]
    return min(values), max(values)


def normalize_date(text: str | None) -> date | None:
    """
    Parse French date strings into a date object.

    Handles: "30/06/2025", "30 juin 2025", "juin 2025", "2025-06-30"
    """
    if not text:
        return None

    text = text.strip()

    # ISO format
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # dd/mm/yyyy or dd-mm-yyyy
    m = re.match(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})", text)
    if m:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))

    text_lower = text.lower()

    # "30 juin 2025"
    m = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text_lower)
    if m:
        month = MONTH_FR.get(m.group(2))
        if month:
            return date(int(m.group(3)), month, int(m.group(1)))

    # "juin 2025"
    m = re.match(r"(\w+)\s+(\d{4})", text_lower)
    if m:
        month = MONTH_FR.get(m.group(1))
        if month:
            return date(int(m.group(2)), month, 1)

    return None
