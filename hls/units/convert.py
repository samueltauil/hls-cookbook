"""Quantity conversion helpers."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from hls.models import Quantity
from hls.units.registry import get_registry
from hls.units.types import IngredientDensityLookup, ParsedQuantity

_MASS_UNITS = {"g", "kg", "mg", "lb", "oz"}
_VOLUME_UNITS = {"ml", "l", "cup", "tbsp", "tsp", "fl_oz", "pinch", "dash"}
_PINT_UNITS = {
    "g": "g",
    "kg": "kg",
    "mg": "mg",
    "ml": "ml",
    "l": "l",
    "lb": "lb",
    "oz": "oz",
    "cup": "cup",
    "tbsp": "tbsp",
    "tsp": "tsp",
    "fl_oz": "fl_oz",
    "pinch": "pinch",
    "dash": "dash",
}
_GRAMS_PER_POUND = Decimal("453.59237")
_ML_PER_CUP = Decimal("236.6")
_ML_PER_TABLESPOON = Decimal("14.8")


def to_metric(
    q: Quantity | ParsedQuantity,
    *,
    ingredient: str = "",
    lookup: IngredientDensityLookup | None = None,
) -> Quantity:
    """Convert a quantity to canonical metric units."""

    quantity = _coerce_quantity(q)
    if _is_non_convertible(quantity):
        return quantity

    if _is_mass(quantity.unit):
        return Quantity(value=_convert(quantity, "g"), unit="g")

    if _is_volume(quantity.unit):
        density = _density_for(ingredient, lookup)
        if density is not None:
            return Quantity(value=_convert(quantity, "ml") * density, unit="g")
        if ingredient.strip():
            return quantity
        return Quantity(value=_convert(quantity, "ml"), unit="ml")

    raise ValueError(f"unsupported unit: {quantity.unit}")


def to_us(
    q: Quantity | ParsedQuantity,
    *,
    ingredient: str = "",
    lookup: IngredientDensityLookup | None = None,
) -> Quantity:
    """Convert a quantity to natural US-customary units by magnitude."""

    del ingredient, lookup
    quantity = _coerce_quantity(q)
    if _is_non_convertible(quantity):
        return quantity

    if _is_mass(quantity.unit):
        grams = _convert(quantity, "g")
        unit = "lb" if grams >= _GRAMS_PER_POUND else "oz"
        return Quantity(value=_round_significant(_convert(quantity, unit)), unit=unit)

    if _is_volume(quantity.unit):
        milliliters = _convert(quantity, "ml")
        if milliliters >= _ML_PER_CUP:
            unit = "cup"
        elif milliliters >= _ML_PER_TABLESPOON:
            unit = "tbsp"
        else:
            unit = "tsp"
        return Quantity(value=_round_significant(_convert(quantity, unit)), unit=unit)

    raise ValueError(f"unsupported unit: {quantity.unit}")


def to_grams(
    q: Quantity,
    *,
    ingredient: str = "",
    lookup: IngredientDensityLookup | None = None,
) -> Decimal | None:
    """Reduce a quantity to grams when enough information is available."""

    if _is_non_convertible(q):
        return None

    if _is_mass(q.unit):
        return _convert(q, "g")

    if _is_volume(q.unit):
        density = _density_for(ingredient, lookup)
        if density is None:
            return None
        return _convert(q, "ml") * density

    raise ValueError(f"unsupported unit: {q.unit}")


def _coerce_quantity(q: Quantity | ParsedQuantity) -> Quantity:
    if isinstance(q, Quantity):
        return q
    return Quantity(value=q.value, unit=q.unit)


def _is_non_convertible(q: Quantity) -> bool:
    return q.unit in {"count", "to_taste"} or q.value is None


def _is_mass(unit: str) -> bool:
    return unit in _MASS_UNITS


def _is_volume(unit: str) -> bool:
    return unit in _VOLUME_UNITS


def _density_for(
    ingredient: str,
    lookup: IngredientDensityLookup | None,
) -> Decimal | None:
    normalized = ingredient.strip()
    if lookup is None or not normalized:
        return None
    return lookup.density_g_per_ml(normalized)


def _convert(q: Quantity, target_unit: str) -> Decimal:
    if q.value is None:
        raise ValueError("cannot convert quantity without a value")
    registry = get_registry()
    converted = registry.Quantity(q.value, _pint_unit(q.unit)).to(_pint_unit(target_unit))
    return Decimal(str(converted.magnitude))


def _pint_unit(unit: str) -> str:
    try:
        return _PINT_UNITS[unit]
    except KeyError as error:
        raise ValueError(f"unsupported unit: {unit}") from error


def _round_significant(value: Decimal, digits: int = 3) -> Decimal:
    if value.is_zero():
        return Decimal("0")
    exponent = value.adjusted() - digits + 1
    quantum = Decimal(1).scaleb(exponent)
    return value.quantize(quantum, rounding=ROUND_HALF_UP)
