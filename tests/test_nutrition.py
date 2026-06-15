"""Nutrition aggregation tests."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from hls.models import (
    Classification,
    Ingredient,
    IngredientMaster,
    IngredientQuantity,
    NutritionPer100g,
    Quantity,
    Recipe,
    RecipeStatus,
    Times,
    Yield,
)
from hls.nutrition import NutritionResult, compute_recipe_nutrition


class FakeNutritionLookup:
    def __init__(self, ingredients: Mapping[str, IngredientMaster]) -> None:
        self._ingredients = ingredients

    def density_g_per_ml(self, ingredient_name: str) -> Decimal | None:
        ingredient = self._ingredients.get(ingredient_name.strip().lower())
        if ingredient is None:
            return None
        return ingredient.density_g_per_ml

    def nutrition_per_100g(self, ingredient_name: str) -> NutritionPer100g | None:
        ingredient = self._ingredients.get(ingredient_name.strip().lower())
        if ingredient is None:
            return None
        return ingredient.nutrition_per_100g


def _ingredient(name: str, value: Decimal | None, unit: str) -> Ingredient:
    return Ingredient(
        name=name,
        quantity=IngredientQuantity(
            metric=Quantity(value=value, unit=unit),
            us=None,
            as_entered=f"{value or ''} {unit}".strip(),
        ),
    )


def _recipe(ingredients: list[Ingredient], *, servings: int = 4) -> Recipe:
    return Recipe(
        status=RecipeStatus.draft,
        title="Test Recipe",
        slug="test-recipe",
        classification=Classification(cuisine="Test"),
        recipe_yield=Yield(servings=servings),
        times=Times(),
        ingredients=ingredients,
    )


def _master(
    name: str,
    *,
    calories: Decimal | None = Decimal("400"),
    protein: Decimal | None = Decimal("10"),
    fat: Decimal | None = Decimal("1"),
    carbs: Decimal | None = Decimal("80"),
    density: Decimal | None = Decimal("0.53"),
) -> IngredientMaster:
    nutrition = None
    if any(value is not None for value in (calories, protein, fat, carbs)):
        nutrition = NutritionPer100g(
            calories_kcal=calories,
            protein_g=protein,
            fat_g=fat,
            carbs_g=carbs,
        )
    return IngredientMaster(
        canonical_name=name,
        display_name=name.replace("_", " "),
        aliases=[],
        nutrition_per_100g=nutrition,
        density_g_per_ml=density,
    )


def test_compute_recipe_nutrition_with_complete_data() -> None:
    recipe = _recipe(
        [
            _ingredient("flour", Decimal("200"), "g"),
            _ingredient("sugar", Decimal("100"), "g"),
        ],
        servings=4,
    )
    lookup = FakeNutritionLookup(
        {
            "flour": _master("flour"),
            "sugar": _master(
                "sugar",
                calories=Decimal("400"),
                protein=Decimal("0"),
                fat=Decimal("0"),
                carbs=Decimal("100"),
            ),
        }
    )

    result = compute_recipe_nutrition(recipe, lookup)

    assert result.missing_ingredients == []
    assert result.skipped_ingredients == []
    assert result.per_serving is not None
    assert result.per_serving.calories_kcal == Decimal("300.0")
    assert result.per_serving.protein_g == Decimal("5.0")
    assert result.per_serving.fat_g == Decimal("0.5")
    assert result.per_serving.carbs_g == Decimal("65.0")


def test_compute_recipe_nutrition_marks_missing_nutrition() -> None:
    recipe = _recipe([_ingredient("flour", Decimal("100"), "g")])
    lookup = FakeNutritionLookup(
        {"flour": _master("flour", calories=None, protein=None, fat=None, carbs=None)}
    )

    result = compute_recipe_nutrition(recipe, lookup)

    assert result == NutritionResult(
        per_serving=None,
        missing_ingredients=["flour"],
        skipped_ingredients=[],
    )


def test_to_taste_and_counts_are_skipped_not_missing() -> None:
    recipe = _recipe(
        [
            _ingredient("flour", Decimal("100"), "g"),
            _ingredient("salt", None, "to_taste"),
            _ingredient("onion", Decimal("1"), "count"),
        ],
        servings=2,
    )
    lookup = FakeNutritionLookup({"flour": _master("flour")})

    result = compute_recipe_nutrition(recipe, lookup)

    assert result.missing_ingredients == []
    assert result.skipped_ingredients == ["salt", "onion"]
    assert result.per_serving is not None
    assert result.per_serving.calories_kcal == Decimal("200.0")


def test_recipe_yield_servings_divides_totals() -> None:
    recipe = _recipe([_ingredient("flour", Decimal("400"), "g")], servings=4)
    lookup = FakeNutritionLookup({"flour": _master("flour")})

    result = compute_recipe_nutrition(recipe, lookup)

    assert result.per_serving is not None
    assert result.per_serving.calories_kcal == Decimal("400.0")
    assert result.per_serving.protein_g == Decimal("10.0")
    assert result.per_serving.fat_g == Decimal("1.0")
    assert result.per_serving.carbs_g == Decimal("80.0")


def test_empty_recipe_returns_zero_nutrition() -> None:
    recipe = _recipe([], servings=4)
    lookup = FakeNutritionLookup({})

    result = compute_recipe_nutrition(recipe, lookup)

    assert result.missing_ingredients == []
    assert result.skipped_ingredients == []
    assert result.per_serving is not None
    assert result.per_serving.calories_kcal == Decimal("0.0")
    assert result.per_serving.protein_g == Decimal("0.0")
    assert result.per_serving.fat_g == Decimal("0.0")
    assert result.per_serving.carbs_g == Decimal("0.0")


def test_volume_ingredient_uses_density_for_grams() -> None:
    recipe = _recipe([_ingredient("flour", Decimal("1"), "cup")], servings=1)
    lookup = FakeNutritionLookup(
        {
            "flour": _master(
                "flour",
                calories=Decimal("100"),
                protein=Decimal("0"),
                fat=Decimal("0"),
                carbs=Decimal("0"),
                density=Decimal("0.5"),
            )
        }
    )

    result = compute_recipe_nutrition(recipe, lookup)

    assert result.per_serving is not None
    assert result.per_serving.calories_kcal == Decimal("118.3")
