"""Validate git-native recipe YAML files."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import yaml
from pydantic import ValidationError

from hls.ingredients_yaml import YamlIngredientLookup
from hls.models import Recipe

_WARNING_PREFIX = "WARNING:"


def validate_recipe_file(path: Path, lookup: YamlIngredientLookup | None = None) -> list[str]:
    """Return validation errors and clearly-prefixed warnings for a recipe file."""

    messages: list[str] = []
    recipe = _load_valid_recipe(path, messages)
    if recipe is None:
        return messages

    expected_name = "recipe.yaml" if recipe.locale in ("", "en") else f"recipe.{recipe.locale}.yaml"
    if path.name != expected_name:
        messages.append(f"{path}: recipe file must be named {expected_name}")
    if path.parent.name != recipe.slug:
        messages.append(
            f"{path}: slug {recipe.slug!r} must match directory name {path.parent.name!r}"
        )

    messages.extend(_duplicate_slug_messages(path, recipe.slug))
    if lookup is not None:
        messages.extend(_ingredient_master_messages(path, recipe, lookup))
    return messages


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate HLS recipe YAML files.")
    parser.add_argument("paths", nargs="*", type=Path, help="Recipe YAML files to validate.")
    parser.add_argument("--ingredients", type=Path, default=Path("data/ingredients.yaml"))
    args = parser.parse_args(argv)

    paths = args.paths or sorted(Path("recipes").glob("*/recipe*.yaml"))
    expanded: list[Path] = []
    for path in paths:
        if path.is_dir():
            expanded.extend(sorted(path.glob("**/recipe*.yaml")))
        else:
            expanded.append(path)
    lookup = YamlIngredientLookup(args.ingredients) if args.ingredients.exists() else None

    messages: list[str] = []
    for path in expanded:
        messages.extend(validate_recipe_file(path, lookup))

    for message in messages:
        print(message)
    return 1 if any(not _is_warning(message) for message in messages) else 0


def _load_valid_recipe(path: Path, messages: list[str]) -> Recipe | None:
    try:
        raw = cast(object, yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    except OSError as error:
        messages.append(f"{path}: could not read YAML: {error}")
        return None
    except yaml.YAMLError as error:
        messages.append(f"{path}: invalid YAML: {error}")
        return None

    try:
        return Recipe.model_validate(raw)
    except ValidationError as error:
        messages.append(f"{path}: recipe model validation failed: {error}")
        return None


def _duplicate_slug_messages(path: Path, slug: str) -> list[str]:
    root = path.parent.parent
    if not root.exists():
        return []

    matches: list[Path] = []
    for recipe_path in sorted(root.glob("*/recipe.yaml")):
        recipe_slug = _raw_slug(recipe_path)
        if recipe_slug == slug:
            matches.append(recipe_path)
    if len(matches) <= 1:
        return []
    joined = ", ".join(str(match) for match in matches)
    return [f"{path}: duplicate slug {slug!r} found in {joined}"]


def _raw_slug(path: Path) -> str | None:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(raw, dict):
        return None
    value = raw.get("slug")
    return value if isinstance(value, str) else None


def _ingredient_master_messages(
    path: Path,
    recipe: Recipe,
    lookup: YamlIngredientLookup,
) -> list[str]:
    messages: list[str] = []
    for ingredient in recipe.ingredients:
        if lookup.ingredient_for(ingredient.name) is None:
            messages.append(
                f"{_WARNING_PREFIX} {path}: ingredient {ingredient.name!r} is not in "
                "data/ingredients.yaml"
            )
    return messages


def _is_warning(message: str) -> bool:
    return message.startswith(_WARNING_PREFIX)


if __name__ == "__main__":
    raise SystemExit(main())
