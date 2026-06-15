"""Shared unit conversion types."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class ParsedQuantity:
    """Quantity parsed from free-form recipe text."""

    value: Decimal | None
    unit: str
    is_range: bool
    range_high: Decimal | None
    raw: str


class IngredientDensityLookup(Protocol):
    """Lookup for ingredient densities in grams per milliliter."""

    def density_g_per_ml(self, ingredient_name: str) -> Decimal | None:
        """Return density for an ingredient, if known."""
