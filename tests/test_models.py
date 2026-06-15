"""Pydantic model validation tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from hls.models import (
    Classification,
    Contributor,
    Ingredient,
    IngredientQuantity,
    Quantity,
    Recipe,
    RecipeStatus,
    Step,
    Times,
    Yield,
)


def _sample_recipe() -> Recipe:
    return Recipe(
        status=RecipeStatus.draft,
        title="Chicken Adobo",
        slug="chicken-adobo",
        summary="Filipino braised chicken.",
        contributor=Contributor(id="user_alias", display_name="Sam Tauil"),
        classification=Classification(
            course="main",
            dietary_tags=["dairy-free"],
            difficulty="easy",
        ),
        recipe_yield=Yield(servings=4),
        times=Times(prep_min=15, cook_min=45, total_min=60),
        ingredients=[
            Ingredient(
                name="chicken thighs",
                quantity=IngredientQuantity(
                    metric=Quantity(value=Decimal("900"), unit="g"),
                    us=Quantity(value=Decimal("2"), unit="lb"),
                    as_entered="2 lb chicken thighs",
                ),
                notes="bone-in",
            )
        ],
        steps=[Step(order=1, text="Simmer until tender.")],
        locales={"en": {"title": "Chicken Adobo"}},
    )


def test_quantity_accepts_decimal_and_string_values() -> None:
    assert Quantity(value=Decimal("1.5"), unit="CUP").value == Decimal("1.5")
    parsed = Quantity(value="2.25", unit="tbsp")
    assert parsed.value == Decimal("2.25")
    assert parsed.unit == "tbsp"


def test_quantity_accepts_to_taste_without_value() -> None:
    quantity = Quantity(value=None, unit="TO_TASTE")
    assert quantity.value is None
    assert quantity.unit == "to_taste"


def test_recipe_round_trips_through_model_dump() -> None:
    recipe = _sample_recipe()
    dumped = recipe.model_dump(by_alias=True)
    assert "yield" in dumped
    round_tripped = Recipe.model_validate(dumped)
    assert round_tripped == recipe


def test_recipe_status_rejects_bad_value() -> None:
    payload = _sample_recipe().model_dump(by_alias=True)
    payload["status"] = "published"
    with pytest.raises(ValidationError):
        Recipe.model_validate(payload)
