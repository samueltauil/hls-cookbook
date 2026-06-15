"""Repository recipe source tests."""

from __future__ import annotations

from pathlib import Path

from hls.ingredients_yaml import YamlIngredientLookup
from hls.normalize import normalize_issue_payload, write_recipe_yaml
from hls.repo_source import load_recipe, load_recipes


def test_load_recipe_round_trips_normalized_recipe(tmp_path: Path) -> None:
    lookup = YamlIngredientLookup(_ingredients_yaml(tmp_path))
    recipe = normalize_issue_payload(
        {
            "title": "Simple Flour Bowl",
            "yield_servings": 2,
            "ingredients": "100 g flour",
            "steps": "Mix flour.",
        },
        lookup,
    )
    path = write_recipe_yaml(recipe, tmp_path / "recipes" / recipe.slug / "recipe.yaml")

    loaded = load_recipe(path)

    assert loaded == recipe
    assert list(load_recipes(tmp_path / "recipes")) == [recipe]


def _ingredients_yaml(tmp_path: Path) -> Path:
    path = tmp_path / "ingredients.yaml"
    path.write_text(
        """
ingredients:
  - canonical_name: flour
    display_name: flour
    aliases: []
    density_g_per_ml: 0.53
    nutrition_per_100g:
      calories_kcal: 400
      protein_g: 10
      fat_g: 1
      carbs_g: 80
""".strip(),
        encoding="utf-8",
    )
    return path
