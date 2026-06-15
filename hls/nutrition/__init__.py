"""Public nutrition aggregation API."""

from __future__ import annotations

from hls.nutrition.aggregate import (
    IngredientNutritionLookup,
    NutritionResult,
    compute_recipe_nutrition,
)

__all__ = [
    "IngredientNutritionLookup",
    "NutritionResult",
    "compute_recipe_nutrition",
]
