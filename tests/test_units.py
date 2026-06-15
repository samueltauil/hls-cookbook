"""Units parsing and conversion tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from hls.models import Quantity
from hls.units import ParsedQuantity, parse_quantity, to_grams, to_metric, to_us


class FakeDensityLookup:
    def __init__(self, densities: dict[str, Decimal]) -> None:
        self._densities = densities

    def density_g_per_ml(self, ingredient_name: str) -> Decimal | None:
        return self._densities.get(ingredient_name.strip().lower())


def _assert_decimal_close(actual: Decimal | None, expected: Decimal, tolerance: Decimal) -> None:
    assert actual is not None
    assert abs(actual - expected) <= tolerance


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("½", Decimal("0.5")),
        ("¼", Decimal("0.25")),
        ("⅓", Decimal("0.3333333333333333333333333333")),
        ("⅔", Decimal("0.6666666666666666666666666667")),
        ("¾", Decimal("0.75")),
        ("⅛", Decimal("0.125")),
        ("⅜", Decimal("0.375")),
        ("⅝", Decimal("0.625")),
        ("⅞", Decimal("0.875")),
    ],
)
def test_parse_vulgar_fractions(text: str, expected: Decimal) -> None:
    parsed = parse_quantity(text)

    _assert_decimal_close(parsed.value, expected, Decimal("0.0000000000000000000000000001"))
    assert parsed.unit == "count"


@pytest.mark.parametrize(
    ("text", "expected", "unit"),
    [
        ("1/2 cup", Decimal("0.5"), "cup"),
        ("3/4 tsp", Decimal("0.75"), "tsp"),
        ("1 1/2 lb", Decimal("1.5"), "lb"),
        ("1 ½ cups", Decimal("1.5"), "cup"),
        ("1½ cups", Decimal("1.5"), "cup"),
    ],
)
def test_parse_plain_and_mixed_fractions(text: str, expected: Decimal, unit: str) -> None:
    parsed = parse_quantity(text)

    assert parsed.value == expected
    assert parsed.unit == unit
    assert not parsed.is_range


@pytest.mark.parametrize(
    ("text", "value", "range_high", "unit"),
    [
        ("2-3 cloves", Decimal("2"), Decimal("3"), "count"),
        ("2\N{EN DASH}3 cloves", Decimal("2"), Decimal("3"), "count"),
        ("1 to 2 cups", Decimal("1"), Decimal("2"), "cup"),
    ],
)
def test_parse_ranges(text: str, value: Decimal, range_high: Decimal, unit: str) -> None:
    parsed = parse_quantity(text)

    assert parsed.value == value
    assert parsed.range_high == range_high
    assert parsed.unit == unit
    assert parsed.is_range


@pytest.mark.parametrize("text", ["to taste", "TO TASTE", "as needed"])
def test_parse_to_taste_phrases(text: str) -> None:
    parsed = parse_quantity(text)

    assert parsed == ParsedQuantity(
        value=None,
        unit="to_taste",
        is_range=False,
        range_high=None,
        raw=text,
    )


@pytest.mark.parametrize(
    ("text", "value"),
    [("1 onion", Decimal("1")), ("2 cloves garlic", Decimal("2")), ("3 eggs", Decimal("3"))],
)
def test_parse_counts(text: str, value: Decimal) -> None:
    parsed = parse_quantity(text)

    assert parsed.value == value
    assert parsed.unit == "count"


@pytest.mark.parametrize(
    ("text", "value", "unit"),
    [
        ("2", Decimal("2"), "count"),
        ("0.5", Decimal("0.5"), "count"),
        ("250ml", Decimal("250"), "ml"),
        ("2 tbsp salt", Decimal("2"), "tbsp"),
        ("a pinch salt", Decimal("1"), "pinch"),
        ("1 T sugar", Decimal("1"), "tbsp"),
    ],
)
def test_parse_common_plain_quantities(text: str, value: Decimal, unit: str) -> None:
    parsed = parse_quantity(text)

    assert parsed.value == value
    assert parsed.unit == unit


def test_parse_unknown_unit_raises_value_error() -> None:
    with pytest.raises(ValueError, match="could not parse quantity"):
        parse_quantity("1 parsec sugar")


def test_mass_round_trip_through_metric_and_us() -> None:
    parsed = parse_quantity("1 lb")

    metric = to_metric(parsed)
    us = to_us(metric)

    assert metric.unit == "g"
    _assert_decimal_close(metric.value, Decimal("453.59237"), Decimal("0.00001"))
    assert us.unit == "lb"
    _assert_decimal_close(us.value, Decimal("1"), Decimal("0.001"))


def test_volume_to_mass_with_density() -> None:
    lookup = FakeDensityLookup({"flour": Decimal("0.53")})
    parsed = parse_quantity("1 cup")

    metric = to_metric(parsed, ingredient="flour", lookup=lookup)
    grams = to_grams(Quantity(value=Decimal("1"), unit="cup"), ingredient="flour", lookup=lookup)

    assert metric.unit == "g"
    _assert_decimal_close(metric.value, Decimal("125.391765345"), Decimal("0.000001"))
    _assert_decimal_close(grams, Decimal("125.391765345"), Decimal("0.000001"))


def test_volume_to_mass_without_density_returns_input_unchanged() -> None:
    lookup = FakeDensityLookup({})
    quantity = Quantity(value=Decimal("1"), unit="cup")

    metric = to_metric(quantity, ingredient="flour", lookup=lookup)
    grams = to_grams(quantity, ingredient="flour", lookup=lookup)

    assert metric == quantity
    assert grams is None


def test_count_and_to_taste_are_not_converted() -> None:
    count = Quantity(value=Decimal("2"), unit="count")
    to_taste = Quantity(value=None, unit="to_taste")

    assert to_metric(count) == count
    assert to_us(count) == count
    assert to_grams(count) is None
    assert to_metric(to_taste) == to_taste
    assert to_us(to_taste) == to_taste
