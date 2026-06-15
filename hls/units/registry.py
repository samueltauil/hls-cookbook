"""Pint registry configured with deterministic culinary units."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pint import UnitRegistry

METRIC_CANONICAL_MASS = "g"
METRIC_CANONICAL_VOLUME = "ml"
US_CANONICAL_MASS = "lb"
US_CANONICAL_VOLUME = "cup"


def _build_registry() -> Any:
    registry: Any = UnitRegistry(system="mks")
    definitions = [
        "cup_us = 236.5882365 * milliliter = cup = cups",
        "tablespoon_us = 14.7867648 * milliliter = tablespoon = tablespoons = tbsp = Tbsp = T",
        "teaspoon_us = 4.92892159 * milliliter = teaspoon = teaspoons = tsp = t",
        "fluid_ounce_us = 29.5735296 * milliliter = fl_oz = floz = fluid_ounce = fluid_ounces",
        "pinch = teaspoon_us / 16",
        "dash = teaspoon_us / 8",
        "pound_us = 453.59237 * gram = lb = lbs",
        "ounce_us = 28.3495231 * gram = oz",
        "count = [] = each = piece = pieces = pc",
        "to_taste = []",
    ]
    for definition in definitions:
        registry.define(definition)
    return registry


@lru_cache(maxsize=1)
def get_registry() -> Any:
    """Return the process-wide Pint registry."""

    return _build_registry()
