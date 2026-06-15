"""Load recipes from the git-native recipe tree."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import cast

import yaml

from hls.models import Recipe


def load_recipe(path: Path) -> Recipe:
    """Load one recipe YAML file."""

    raw = cast(object, yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    return Recipe.model_validate(raw)


def load_recipes(root: Path = Path("recipes"), locale: str = "en") -> Iterator[Recipe]:
    """Yield recipes from ``<root>/<slug>/recipe[.<locale>].yaml`` files.

    For each recipe directory, prefers the locale-specific variant
    ``recipe.<locale>.yaml`` when it exists; otherwise falls back to
    the default ``recipe.yaml``. Pass ``locale="en"`` (the default) to
    always use the base file.
    """

    if not root.exists():
        return
    for recipe_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        default_file = recipe_dir / "recipe.yaml"
        variant_file = recipe_dir / f"recipe.{locale}.yaml"
        target = variant_file if (locale != "en" and variant_file.is_file()) else default_file
        if target.is_file():
            yield load_recipe(target)
