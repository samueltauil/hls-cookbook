"""YAML ingredient lookup tests."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from hls.ingredients_yaml import YamlIngredientLookup


def test_yaml_lookup_matches_canonical_alias_and_missing(tmp_path: Path) -> None:
    path = tmp_path / "ingredients.yaml"
    path.write_text(
        """
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
""".strip(),
        encoding="utf-8",
    )

    lookup = YamlIngredientLookup(path)

    assert lookup.ingredient_for(" chicken_thigh ") is not None
    alias_match = lookup.ingredient_for("CHICKEN THIGHS")
    assert alias_match is not None
    assert alias_match.canonical_name == "chicken_thigh"
    assert lookup.density_g_per_ml("chicken thighs") is None
    assert lookup.nutrition_per_100g("boneless chicken thigh") is not None
    assert lookup.nutrition_per_100g("missing") is None
    assert lookup.ingredient_for("missing") is None
    assert alias_match.nutrition_per_100g is not None
    assert alias_match.nutrition_per_100g.calories_kcal == Decimal("209")
