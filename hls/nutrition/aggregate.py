"""Per-recipe nutrition aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol

from hls.models import NutritionFacts, NutritionPer100g, Recipe
from hls.units import to_grams


class IngredientNutritionLookup(Protocol):
    """Lookup for density and nutrition data by ingredient name."""

    def density_g_per_ml(self, ingredient_name: str) -> Decimal | None:
        """Return density for an ingredient, if known."""

    def nutrition_per_100g(self, ingredient_name: str) -> NutritionPer100g | None:
        """Return nutrition per 100 g for an ingredient, if known."""


@dataclass(frozen=True)
class NutritionResult:
    """Computed nutrition and completeness details for a recipe."""

    per_serving: NutritionFacts | None
    missing_ingredients: list[str]
    skipped_ingredients: list[str]


def compute_recipe_nutrition(
    recipe: Recipe,
    lookup: IngredientNutritionLookup,
) -> NutritionResult:
    """Compute per-serving nutrition facts for a recipe."""

    totals = NutritionFacts(
        calories_kcal=Decimal("0"),
        protein_g=Decimal("0"),
        fat_g=Decimal("0"),
        carbs_g=Decimal("0"),
    )
    missing_ingredients: list[str] = []
    skipped_ingredients: list[str] = []

    for ingredient in recipe.ingredients:
        quantity = ingredient.quantity.metric or ingredient.quantity.us
        if quantity is None:
            _append_unique(missing_ingredients, ingredient.name)
            continue

        if quantity.unit == "to_taste" or quantity.value is None:
            _append_unique(skipped_ingredients, ingredient.name)
            continue
        if quantity.unit == "count":
            _append_unique(skipped_ingredients, ingredient.name)
            continue

        grams = to_grams(quantity, ingredient=ingredient.name, lookup=lookup)
        if grams is None:
            _append_unique(missing_ingredients, ingredient.name)
            continue

        nutrition = lookup.nutrition_per_100g(ingredient.name)
        if nutrition is None or not _is_complete(nutrition):
            _append_unique(missing_ingredients, ingredient.name)
            continue

        _add_scaled(totals, nutrition, grams)

    if missing_ingredients:
        return NutritionResult(
            per_serving=None,
            missing_ingredients=missing_ingredients,
            skipped_ingredients=skipped_ingredients,
        )

    servings = Decimal(recipe.recipe_yield.servings)
    return NutritionResult(
        per_serving=_per_serving(totals, servings),
        missing_ingredients=missing_ingredients,
        skipped_ingredients=skipped_ingredients,
    )


def _is_complete(nutrition: NutritionPer100g) -> bool:
    return all(
        value is not None
        for value in (
            nutrition.calories_kcal,
            nutrition.protein_g,
            nutrition.fat_g,
            nutrition.carbs_g,
        )
    )


def _add_scaled(totals: NutritionFacts, nutrition: NutritionPer100g, grams: Decimal) -> None:
    factor = grams / Decimal("100")
    totals.calories_kcal = (
        _require_decimal(totals.calories_kcal) + _require_decimal(nutrition.calories_kcal) * factor
    )
    totals.protein_g = (
        _require_decimal(totals.protein_g) + _require_decimal(nutrition.protein_g) * factor
    )
    totals.fat_g = _require_decimal(totals.fat_g) + _require_decimal(nutrition.fat_g) * factor
    totals.carbs_g = _require_decimal(totals.carbs_g) + _require_decimal(nutrition.carbs_g) * factor


def _per_serving(totals: NutritionFacts, servings: Decimal) -> NutritionFacts:
    return NutritionFacts(
        calories_kcal=_quantize_one(_require_decimal(totals.calories_kcal) / servings),
        protein_g=_quantize_one(_require_decimal(totals.protein_g) / servings),
        fat_g=_quantize_one(_require_decimal(totals.fat_g) / servings),
        carbs_g=_quantize_one(_require_decimal(totals.carbs_g) / servings),
    )


def _quantize_one(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _require_decimal(value: Decimal | None) -> Decimal:
    if value is None:
        raise ValueError("nutrition data is incomplete")
    return value


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)
