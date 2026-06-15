"""Parser for recipe ingredient quantities."""

from __future__ import annotations

import re
from decimal import Decimal, localcontext

from hls.units.types import ParsedQuantity

_VULGAR_FRACTIONS: dict[str, tuple[int, int]] = {
    "½": (1, 2),
    "¼": (1, 4),
    "⅓": (1, 3),
    "⅔": (2, 3),
    "¾": (3, 4),
    "⅛": (1, 8),
    "⅜": (3, 8),
    "⅝": (5, 8),
    "⅞": (7, 8),
}

_NUMBER_PATTERN = r"(?:\d+(?:\.\d+)?\s+\d+\s*/\s*\d+|\d+\s*/\s*\d+|\d+(?:\.\d+)?)"
_RANGE_HYPHEN_RE = re.compile(
    rf"^(?P<low>{_NUMBER_PATTERN})\s*-\s*(?P<high>{_NUMBER_PATTERN})(?P<rest>.*)$"
)
_RANGE_TO_RE = re.compile(
    rf"^(?P<low>{_NUMBER_PATTERN})\s+to\s+(?P<high>{_NUMBER_PATTERN})(?P<rest>.*)$",
    re.IGNORECASE,
)
_SINGLE_RE = re.compile(rf"^(?P<number>{_NUMBER_PATTERN})(?P<rest>.*)$")

_UNIT_SYNONYMS = {
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "mg": "mg",
    "milligram": "mg",
    "milligrams": "mg",
    "ml": "ml",
    "milliliter": "ml",
    "milliliters": "ml",
    "millilitre": "ml",
    "millilitres": "ml",
    "l": "l",
    "liter": "l",
    "liters": "l",
    "litre": "l",
    "litres": "l",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
    "oz": "oz",
    "ounce": "oz",
    "ounces": "oz",
    "cup": "cup",
    "cups": "cup",
    "tbsp": "tbsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tbs": "tbsp",
    "tbsps": "tbsp",
    "tsp": "tsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "pinch": "pinch",
    "pinches": "pinch",
    "dash": "dash",
    "dashes": "dash",
    "floz": "fl_oz",
    "fl_oz": "fl_oz",
    "fluidounce": "fl_oz",
    "count": "count",
    "each": "count",
    "piece": "count",
    "pieces": "count",
    "pc": "count",
}
_TWO_TOKEN_UNITS = {
    "fl oz": "fl_oz",
    "fluid oz": "fl_oz",
    "fluid ounce": "fl_oz",
    "fluid ounces": "fl_oz",
}
_COUNT_NOUNS = {
    "apple",
    "apples",
    "banana",
    "bananas",
    "carrot",
    "carrots",
    "clove",
    "cloves",
    "egg",
    "eggs",
    "garlic",
    "onion",
    "onions",
    "pepper",
    "peppers",
    "shallot",
    "shallots",
    "tomato",
    "tomatoes",
}
_TO_TASTE_PHRASES = {"to taste", "as needed"}
_UNIT_LEADING_ONE = {"pinch", "pinches", "dash", "dashes"}


def parse_quantity(text: str) -> ParsedQuantity:
    """Parse free-form quantity text into a canonical quantity."""

    raw = text
    normalized = _normalize_text(text)
    if not normalized:
        raise ValueError(f"could not parse quantity: {raw}")

    lowered = normalized.lower()
    if lowered in _TO_TASTE_PHRASES:
        return ParsedQuantity(
            value=None,
            unit="to_taste",
            is_range=False,
            range_high=None,
            raw=raw,
        )

    normalized = _apply_leading_one(normalized)
    normalized = _replace_vulgar_fractions(normalized)

    range_match = _RANGE_TO_RE.match(normalized) or _RANGE_HYPHEN_RE.match(normalized)
    if range_match is not None:
        value = _parse_decimal(range_match.group("low"))
        high = _parse_decimal(range_match.group("high"))
        unit = _parse_unit(range_match.group("rest"), raw)
        return ParsedQuantity(value=value, unit=unit, is_range=True, range_high=high, raw=raw)

    single_match = _SINGLE_RE.match(normalized)
    if single_match is None:
        raise ValueError(f"could not parse quantity: {raw}")

    return ParsedQuantity(
        value=_parse_decimal(single_match.group("number")),
        unit=_parse_unit(single_match.group("rest"), raw),
        is_range=False,
        range_high=None,
        raw=raw,
    )


def _normalize_text(text: str) -> str:
    normalized = text.strip().replace("\N{EN DASH}", "-").replace("\N{EM DASH}", "-")
    return re.sub(r"\s+", " ", normalized)


def _apply_leading_one(text: str) -> str:
    lowered = text.lower()
    if lowered.startswith("a "):
        return f"1 {text[2:]}"
    if lowered.startswith("an "):
        return f"1 {text[3:]}"
    first = lowered.split(" ", maxsplit=1)[0]
    if first in _UNIT_LEADING_ONE:
        return f"1 {text}"
    return text


def _replace_vulgar_fractions(text: str) -> str:
    pieces: list[str] = []
    for character in text:
        fraction = _VULGAR_FRACTIONS.get(character)
        if fraction is None:
            pieces.append(character)
        else:
            numerator, denominator = fraction
            pieces.append(f" {numerator}/{denominator} ")
    return re.sub(r"\s+", " ", "".join(pieces)).strip()


def _parse_decimal(value: str) -> Decimal:
    parts = value.strip().split()
    if len(parts) == 2 and "/" in parts[1]:
        return Decimal(parts[0]) + _parse_fraction(parts[1])
    if len(parts) == 1 and "/" in parts[0]:
        return _parse_fraction(parts[0])
    return Decimal(value.strip())


def _parse_fraction(value: str) -> Decimal:
    numerator_text, denominator_text = (part.strip() for part in value.split("/", maxsplit=1))
    numerator = Decimal(numerator_text)
    denominator = Decimal(denominator_text)
    if denominator == 0:
        raise ValueError("fraction denominator must not be zero")
    with localcontext() as context:
        context.prec = 28
        return numerator / denominator


def _parse_unit(rest: str, raw: str) -> str:
    cleaned = rest.strip()
    if not cleaned:
        return "count"

    tokens = [token.strip(".,;:()[]{}") for token in cleaned.split()]
    tokens = [token for token in tokens if token]
    if not tokens:
        return "count"

    if len(tokens) >= 2:
        two_token = f"{tokens[0].lower()} {tokens[1].lower()}"
        unit = _TWO_TOKEN_UNITS.get(two_token)
        if unit is not None:
            return unit

    first = tokens[0]
    if first == "T":
        return "tbsp"

    normalized = first.lower().replace(".", "").replace("-", "_")
    unit = _UNIT_SYNONYMS.get(normalized)
    if unit is not None:
        return unit

    if normalized in _COUNT_NOUNS:
        return "count"

    raise ValueError(f"could not parse quantity: {raw}")
