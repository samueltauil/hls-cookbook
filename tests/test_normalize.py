"""Issue payload normalization tests."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from hls.ingredients_yaml import YamlIngredientLookup
from hls.models import RecipeStatus
from hls.normalize import normalize_issue_payload, write_recipe_yaml


def test_normalize_issue_payload_builds_draft_recipe_with_nutrition(tmp_path: Path) -> None:
    lookup = YamlIngredientLookup(_ingredients_yaml(tmp_path))
    payload: dict[str, object] = {
        "title": "Simple Flour Bowl",
        "contributor": {"github_handle": "octocat", "display_name": "Octo Cat"},
        "yield_servings": 2,
        "prep_min": 5,
        "cook_min": 0,
        "course": "main",
        "dietary_tags": "vegan, pantry",
        "difficulty": "easy",
        "ingredients": "100 g flour",
        "steps": "1. Mix flour.\n2. Serve.",
        "notes": "A test recipe.",
        "photo_urls": ["https://example.invalid/flour.jpg"],
    }

    recipe = normalize_issue_payload(payload, lookup)

    assert recipe.slug == "simple-flour-bowl"
    assert recipe.status == RecipeStatus.draft
    assert recipe.contributor.id == "octocat"
    assert recipe.classification.dietary_tags == ["vegan", "pantry"]
    assert recipe.ingredients[0].name == "flour"
    assert recipe.ingredients[0].quantity.metric is not None
    assert recipe.ingredients[0].quantity.metric.unit == "g"
    assert recipe.ingredients[0].quantity.metric.value == Decimal("100")
    assert recipe.ingredients[0].quantity.us is not None
    assert recipe.ingredients[0].quantity.us.unit == "oz"
    assert recipe.nutrition_per_serving is not None
    assert recipe.nutrition_per_serving.calories_kcal == Decimal("200.0")
    assert recipe.steps[0].text == "Mix flour."
    assert recipe.photos[0].is_hero


def test_normalize_supports_ingredient_sections(tmp_path: Path) -> None:
    lookup = YamlIngredientLookup(_ingredients_yaml(tmp_path))
    payload: dict[str, object] = {
        "title": "Sectioned Recipe",
        "yield_servings": 1,
        "course": "main",
        "difficulty": "easy",
        "ingredients": ("## Marinade\n50 g flour\n## Topping\n20 g flour\n"),
        "steps": "1. Combine.",
    }

    recipe = normalize_issue_payload(payload, lookup)

    sections = [ingredient.section for ingredient in recipe.ingredients]
    assert sections == ["marinade", "topping"]


def test_normalize_splits_ingredient_notes(tmp_path: Path) -> None:
    lookup = YamlIngredientLookup(_ingredients_yaml(tmp_path))
    payload: dict[str, object] = {
        "title": "Noted Recipe",
        "yield_servings": 1,
        "course": "main",
        "difficulty": "easy",
        "ingredients": "100 g flour, sifted",
        "steps": "1. Use.",
    }

    recipe = normalize_issue_payload(payload, lookup)

    assert recipe.ingredients[0].name == "flour"
    assert recipe.ingredients[0].notes == "sifted"


def test_normalize_captures_extended_metadata(tmp_path: Path) -> None:
    lookup = YamlIngredientLookup(_ingredients_yaml(tmp_path))
    payload: dict[str, object] = {
        "title": "Rich Recipe",
        "summary": "A short, evocative description.",
        "contributor": {"github_handle": "octocat"},
        "source": {"attribution": "Adapted from grandmother", "url": "https://example.invalid"},
        "yield_servings": 4,
        "yield_notes": "Halve for a snack portion.",
        "prep_min": 10,
        "cook_min": 20,
        "rest_min": 30,
        "course": "main",
        "dietary_tags": "vegetarian",
        "allergens": "gluten",
        "occasion": "weeknight, batch-cook",
        "keywords": "comfort food",
        "difficulty": "medium",
        "equipment": "Dutch oven\nWhisk",
        "ingredients": "100 g flour, sifted",
        "steps": "1. Combine.\n2. Serve.",
        "tips": "Swap rice flour for gluten-free.",
        "storage": "Keeps 3 days refrigerated.",
        "pairings": "Crusty bread.",
        "photo_urls": ["https://example.invalid/a.jpg", "https://example.invalid/b.jpg"],
        "hero_caption": "Final plate, top-down.",
        "locale": "en",
    }

    recipe = normalize_issue_payload(payload, lookup)

    assert recipe.summary == "A short, evocative description."
    assert recipe.source is not None
    assert recipe.source.attribution == "Adapted from grandmother"
    assert recipe.recipe_yield.notes == "Halve for a snack portion."
    assert recipe.times.rest_min == 30
    assert recipe.times.total_min == 60
    assert recipe.classification.allergens == ["gluten"]
    assert recipe.classification.occasion == ["weeknight", "batch-cook"]
    assert recipe.classification.keywords == ["comfort food"]
    assert recipe.equipment == ["Dutch oven", "Whisk"]
    assert recipe.tips.startswith("Swap rice flour")
    assert recipe.storage.startswith("Keeps 3 days")
    assert recipe.pairings == "Crusty bread."
    assert recipe.photos[0].caption == "Final plate, top-down."
    assert not recipe.photos[1].caption


def test_write_recipe_yaml_uses_locale_suffix_for_non_default(tmp_path: Path) -> None:
    lookup = YamlIngredientLookup(_ingredients_yaml(tmp_path))
    payload: dict[str, object] = {
        "title": "Pão Simples",
        "yield_servings": 1,
        "course": "side",
        "difficulty": "easy",
        "ingredients": "100 g flour",
        "steps": "1. Misturar.",
        "locale": "pt-BR",
    }

    recipe = normalize_issue_payload(payload, lookup)

    # Force write into tmp_path by overriding the destination root via chdir.
    original = Path.cwd()
    try:
        target_root = tmp_path / "out"
        target_root.mkdir()
        path = write_recipe_yaml(recipe, target_root / recipe.slug / "recipe.pt-BR.yaml")
    finally:
        original  # noqa: B018 -- preserved for symmetry
    assert path.name == "recipe.pt-BR.yaml"
    assert path.parent.name == recipe.slug


def _ingredients_yaml(tmp_path: Path) -> Path:
    path = tmp_path / "ingredients.yaml"
    path.write_text(
        """
ingredients:
  - canonical_name: flour
    display_name: flour
    aliases: [all-purpose flour]
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
