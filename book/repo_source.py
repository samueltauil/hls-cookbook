"""Load book-eligible recipes from the git-native repository layout."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from importlib import import_module
from pathlib import Path
from typing import cast

import yaml

from hls.models.recipe import Recipe, RecipeStatus

ROOT = Path(__file__).resolve().parents[1]
RECIPES_DIR = ROOT / "recipes"
BOOK_ELIGIBLE_STATUSES = {RecipeStatus.approved}


def load_recipes(
    *, edition: str = "preview", locale: str = "en", recipes_dir: Path | None = None
) -> list[Recipe]:
    """Return approved recipes that should appear in the requested book edition."""
    source_dir = recipes_dir or RECIPES_DIR
    recipes = _load_all_recipes(source_dir, locale=locale)
    return [recipe for recipe in recipes if _is_book_eligible(recipe, edition)]


def _load_all_recipes(recipes_dir: Path, *, locale: str = "en") -> list[Recipe]:
    loader = _hls_loader()
    if loader is not None:
        return _call_hls_loader(loader, recipes_dir, locale=locale)
    return _fallback_load_recipes(recipes_dir, locale=locale)


def _hls_loader() -> Callable[..., Iterable[Recipe]] | None:
    try:
        module = import_module("hls.repo_source")
    except ModuleNotFoundError as exc:
        if exc.name == "hls.repo_source":
            return None
        raise
    loader = getattr(module, "load_recipes", None)
    if not callable(loader):
        return None
    return cast(Callable[..., Iterable[Recipe]], loader)


def _call_hls_loader(
    loader: Callable[..., Iterable[Recipe]], recipes_dir: Path, *, locale: str = "en"
) -> list[Recipe]:
    attempts: list[Callable[[], Iterable[Recipe]]] = [
        lambda: loader(recipes_dir, locale=locale),
        lambda: loader(recipes_dir=recipes_dir, locale=locale),
        lambda: loader(recipes_dir),
        lambda: loader(),
    ]
    loaded: Iterable[Recipe] | None = None
    for attempt in attempts:
        try:
            loaded = attempt()
            break
        except TypeError:
            continue
    if loaded is None:
        raise TypeError("could not invoke hls.repo_source.load_recipes")
    return [
        recipe if isinstance(recipe, Recipe) else Recipe.model_validate(recipe) for recipe in loaded
    ]


def _fallback_load_recipes(recipes_dir: Path, *, locale: str = "en") -> list[Recipe]:
    recipes: list[Recipe] = []
    if not recipes_dir.exists():
        return recipes
    for recipe_dir in sorted(p for p in recipes_dir.iterdir() if p.is_dir()):
        default_file = recipe_dir / "recipe.yaml"
        variant_file = recipe_dir / f"recipe.{locale}.yaml"
        target = variant_file if (locale != "en" and variant_file.is_file()) else default_file
        if not target.is_file():
            continue
        data = yaml.safe_load(target.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            recipes.append(Recipe.model_validate(data))
    return recipes


def _is_book_eligible(recipe: Recipe, edition: str) -> bool:
    if recipe.status not in BOOK_ELIGIBLE_STATUSES:
        return False
    if edition == "preview":
        return True
    return edition in recipe.book.included_in_editions
