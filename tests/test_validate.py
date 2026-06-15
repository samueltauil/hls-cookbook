"""Recipe YAML validation tests."""

from __future__ import annotations

from pathlib import Path

from hls.ingredients_yaml import YamlIngredientLookup
from hls.normalize import normalize_issue_payload, write_recipe_yaml
from hls.validate import validate_recipe_file


def test_validate_recipe_file_accepts_valid_recipe(tmp_path: Path) -> None:
    lookup = YamlIngredientLookup(_ingredients_yaml(tmp_path))
    recipe = normalize_issue_payload(_payload(), lookup)
    path = write_recipe_yaml(recipe, tmp_path / recipe.slug / "recipe.yaml")

    assert validate_recipe_file(path, lookup) == []


def test_validate_recipe_file_reports_model_and_slug_errors(tmp_path: Path) -> None:
    invalid_model_path = tmp_path / "bad" / "recipe.yaml"
    invalid_model_path.parent.mkdir()
    invalid_model_path.write_text("title: Missing required fields\n", encoding="utf-8")

    model_errors = validate_recipe_file(invalid_model_path)

    assert any("recipe model validation failed" in error for error in model_errors)

    lookup = YamlIngredientLookup(_ingredients_yaml(tmp_path))
    recipe = normalize_issue_payload(_payload(), lookup)
    slug_mismatch_path = write_recipe_yaml(recipe, tmp_path / "wrong-slug" / "recipe.yaml")

    slug_errors = validate_recipe_file(slug_mismatch_path, lookup)

    assert any("must match directory name" in error for error in slug_errors)


def test_validate_recipe_file_flags_unknown_ingredients_as_warning(tmp_path: Path) -> None:
    lookup = YamlIngredientLookup(_ingredients_yaml(tmp_path))
    recipe = normalize_issue_payload(_payload(), lookup)
    recipe.ingredients[0].name = "unknown ingredient"
    path = write_recipe_yaml(recipe, tmp_path / recipe.slug / "recipe.yaml")

    messages = validate_recipe_file(path, lookup)

    assert messages == [
        f"WARNING: {path}: ingredient 'unknown ingredient' is not in data/ingredients.yaml"
    ]


def _payload() -> dict[str, object]:
    return {
        "title": "Simple Flour Bowl",
        "yield_servings": 2,
        "ingredients": "100 g flour",
        "steps": "Mix flour.",
    }


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
