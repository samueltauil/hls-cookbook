"""YAML-backed ingredient master lookup.

Ingredient master files use this schema::

    ingredients:
      - canonical_name: chicken_thigh
        display_name: chicken thigh
        aliases: [chicken thighs, boneless chicken thigh]
        density_g_per_ml: null
        nutrition_per_100g:
          calories_kcal: 209
          protein_g: 26
          fat_g: 11
          carbs_g: 0

Names are matched by ``canonical_name`` or any alias, case-insensitively after trimming.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import cast

import yaml
from pydantic import BaseModel, ConfigDict, Field

from hls.models import IngredientMaster, NutritionPer100g


class IngredientMasterFile(BaseModel):
    """Top-level ``data/ingredients.yaml`` document."""

    model_config = ConfigDict(extra="forbid")

    ingredients: list[IngredientMaster] = Field(default_factory=list)


class YamlIngredientLookup:
    """Cached lookup for ingredient density and nutrition metadata."""

    def __init__(self, path: Path = Path("data/ingredients.yaml")) -> None:
        self.path = path
        document = _load_document(path)
        self.ingredients = tuple(document.ingredients)
        self._index = _build_index(self.ingredients)

    def ingredient_for(self, ingredient_name: str) -> IngredientMaster | None:
        """Return the matched ingredient master entry, if known."""

        return self._index.get(_normalize_key(ingredient_name))

    def canonical_name(self, ingredient_name: str) -> str | None:
        """Return the canonical ingredient name for an input name, if known."""

        ingredient = self.ingredient_for(ingredient_name)
        if ingredient is None:
            return None
        return ingredient.canonical_name

    def density_g_per_ml(self, ingredient_name: str) -> Decimal | None:
        """Return density for an ingredient, if known."""

        ingredient = self.ingredient_for(ingredient_name)
        if ingredient is None:
            return None
        return ingredient.density_g_per_ml

    def nutrition_per_100g(self, ingredient_name: str) -> NutritionPer100g | None:
        """Return nutrition per 100 g for an ingredient, if known."""

        ingredient = self.ingredient_for(ingredient_name)
        if ingredient is None:
            return None
        return ingredient.nutrition_per_100g


def _load_document(path: Path) -> IngredientMasterFile:
    raw = cast(object, yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    return IngredientMasterFile.model_validate(raw)


def _build_index(ingredients: tuple[IngredientMaster, ...]) -> dict[str, IngredientMaster]:
    index: dict[str, IngredientMaster] = {}
    for ingredient in ingredients:
        for name in (ingredient.canonical_name, *ingredient.aliases):
            key = _normalize_key(name)
            if not key:
                continue
            existing = index.get(key)
            if existing is not None and existing.canonical_name != ingredient.canonical_name:
                raise ValueError(
                    f"ingredient lookup key {name!r} maps to both "
                    f"{existing.canonical_name!r} and {ingredient.canonical_name!r}"
                )
            index[key] = ingredient
    return index


def _normalize_key(value: str) -> str:
    return value.strip().lower()
