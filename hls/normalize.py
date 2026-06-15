"""Normalize GitHub Issue Form recipe payloads into recipe YAML.

Expected issue JSON shape (all fields optional except marked **required**)::

    {
      "title": "Chicken Adobo",                          # required
      "summary": "Filipino braise of soy, vinegar, garlic.",
      "contributor": {"github_handle": "octocat", "display_name": "Octo Cat"},
      "source": {"attribution": "Adapted from Lola Maria", "url": "https://..."},
      "yield_servings": 4,                                # required
      "yield_notes": "Generous mains; halve for snacks.",
      "prep_min": 15,
      "cook_min": 45,
      "rest_min": 30,
      "course": "main",                                   # required
      "dietary_tags": "dairy-free, gluten-free",
      "allergens": ["soy"],
      "occasion": "weeknight",
      "keywords": "braise, comfort food",
      "difficulty": "easy",                               # required
      "equipment": "Dutch oven, tongs",
      "ingredients": "## Marinade\\n1/4 cup soy sauce\\n\\n## Braise\\n2 lb chicken thighs, bone-in",
      "steps": "1. Marinate.\\n\\n2. Brown.",            # required
      "tips": "Use cane vinegar if you can find it.",
      "storage": "Keeps 4 days refrigerated.",
      "pairings": "Steamed jasmine rice.",
      "notes": "Long-form notes that don't fit elsewhere.",
      "photo_urls": ["https://example.invalid/photo.jpg"],
      "hero_caption": "Chicken adobo over rice.",
      "locale": "en"
    }
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from importlib import import_module
from pathlib import Path
from typing import Any, cast

import yaml

from hls.ingredients_yaml import YamlIngredientLookup
from hls.models import (
    Classification,
    Contributor,
    Ingredient,
    IngredientQuantity,
    Photo,
    Recipe,
    RecipeStatus,
    Source,
    Step,
    Times,
    Yield,
)
from hls.nutrition import compute_recipe_nutrition
from hls.units import ParsedQuantity, parse_quantity, to_metric, to_us

_QUANTITY_PREFIX_RE = re.compile(
    r"^\s*(?:\d+(?:\.\d+)?\s+\d+\s*/\s*\d+|\d+\s*/\s*\d+|\d+(?:\.\d+)?|[½¼⅓⅔¾⅛⅜⅝⅞])\s*",
    re.IGNORECASE,
)
_UNIT_PREFIX_RE = re.compile(
    r"^(?:g|grams?|kg|kilograms?|mg|milligrams?|ml|milliliters?|millilitres?|l|liters?|litres?|lb|lbs|pounds?|oz|ounces?|cups?|tbsp|tablespoons?|tbsps?|tsp|teaspoons?|pinches?|dashes?|fl\s*oz|fluid\s+ounces?|count|each|pieces?|pc)\b\s*",
    re.IGNORECASE,
)
_STEP_NUMBER_RE = re.compile(r"^\s*\d+[.)]\s*")
_SLUG_RE = re.compile(r"[^a-z0-9]+")
_SECTION_HEADER_RE = re.compile(r"^\s*#{1,6}\s+(.+?)\s*$")


def normalize_issue_payload(payload: dict[str, object], lookup: YamlIngredientLookup) -> Recipe:
    """Normalize a parsed issue-form payload into a draft recipe model."""

    title = _required_string(payload, "title")
    slug = _slugify(title)
    prep_min = _int_value(payload.get("prep_min"), default=0)
    cook_min = _int_value(payload.get("cook_min"), default=0)
    rest_min = _int_value(payload.get("rest_min"), default=0)

    summary = _string_value(payload.get("summary")) or _string_value(payload.get("notes"))

    recipe = Recipe(
        id=_new_recipe_id(),
        status=RecipeStatus.draft,
        title=title,
        slug=slug,
        summary=summary,
        contributor=_contributor(payload.get("contributor")),
        classification=Classification(
            course=_string_value(payload.get("course"), default="main"),
            dietary_tags=_csv_list(payload.get("dietary_tags")),
            allergens=_csv_list(payload.get("allergens")),
            keywords=_csv_list(payload.get("keywords")),
            difficulty=_string_value(payload.get("difficulty"), default="easy"),
            occasion=_csv_list(payload.get("occasion")),
        ),
        recipe_yield=Yield(
            servings=_int_value(payload.get("yield_servings"), default=1),
            notes=_string_value(payload.get("yield_notes")),
        ),
        times=Times(
            prep_min=prep_min,
            cook_min=cook_min,
            rest_min=rest_min,
            total_min=prep_min + cook_min + rest_min,
        ),
        ingredients=_ingredients(_string_value(payload.get("ingredients")), lookup),
        steps=_steps(_string_value(payload.get("steps"))),
        photos=_photos(payload.get("photo_urls"), _string_value(payload.get("hero_caption"))),
        equipment=_lines_or_csv(payload.get("equipment")),
        tips=_string_value(payload.get("tips")),
        storage=_string_value(payload.get("storage")),
        pairings=_string_value(payload.get("pairings")),
        source=_source(payload.get("source")),
        locale=_string_value(payload.get("locale"), default="en"),
    )
    recipe.nutrition_per_serving = compute_recipe_nutrition(recipe, lookup).per_serving
    return recipe


def write_recipe_yaml(recipe: Recipe, path: Path | None = None) -> Path:
    """Write normalized recipe YAML and return the destination path."""

    if path is None:
        suffix = "recipe.yaml" if recipe.locale in ("", "en") else f"recipe.{recipe.locale}.yaml"
        destination = Path("recipes") / recipe.slug / suffix
    else:
        destination = path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        yaml.safe_dump(
            recipe.model_dump(mode="json", by_alias=True, exclude_none=True),
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return destination


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize an HLS recipe issue payload.")
    parser.add_argument("--issue-json", required=True, help="Path to issue JSON, or '-' for stdin.")
    parser.add_argument("--out", type=Path, help="Output recipe.yaml path.")
    parser.add_argument("--ingredients", type=Path, default=Path("data/ingredients.yaml"))
    args = parser.parse_args(argv)

    payload = _read_payload(args.issue_json)
    lookup = YamlIngredientLookup(args.ingredients)
    recipe = normalize_issue_payload(payload, lookup)
    output_path = write_recipe_yaml(recipe, args.out)
    print(output_path)
    return 0


def _read_payload(source: str) -> dict[str, object]:
    text = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    raw = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError("issue JSON must be an object")
    return cast(dict[str, object], raw)


def _new_recipe_id() -> str:
    ulid_module = import_module("ulid")
    new_ulid = getattr(ulid_module, "new", None)
    if callable(new_ulid):
        return f"rcp_{new_ulid()}"
    ulid_class = cast(type[Any], ulid_module.ULID)
    return f"rcp_{ulid_class()}"


def _contributor(value: object) -> Contributor:
    if not isinstance(value, dict):
        return Contributor()
    github_handle = _string_value(value.get("github_handle"))
    display_name = _string_value(value.get("display_name"))
    return Contributor(id=github_handle or None, display_name=display_name)


def _source(value: object) -> Source | None:
    if isinstance(value, str):
        text = value.strip()
        return Source(attribution=text) if text else None
    if isinstance(value, dict):
        attribution = _string_value(value.get("attribution"))
        url = _string_value(value.get("url"))
        if attribution or url:
            return Source(attribution=attribution, url=url)
    return None


def _ingredients(text: str, lookup: YamlIngredientLookup) -> list[Ingredient]:
    """Parse the ingredients textarea.

    Supports ``## Section`` headers (any level of leading ``#``) to group
    ingredients. Lines after a header land in that section until the next
    header. The first un-headered line goes in the ``main`` section.
    Trailing ", note" on a line is split into ``Ingredient.notes``.
    """

    ingredients: list[Ingredient] = []
    current_section = "main"
    for line in _non_empty_lines(text):
        header_match = _SECTION_HEADER_RE.match(line)
        if header_match:
            current_section = header_match.group(1).strip().lower() or "main"
            continue
        parsed = parse_quantity(line)
        name, notes = _ingredient_name_and_notes(line, parsed)
        metric = to_metric(parsed, ingredient=name, lookup=lookup)
        us = to_us(parsed, ingredient=name, lookup=lookup)
        ingredients.append(
            Ingredient(
                name=name,
                section=current_section,
                notes=notes,
                quantity=IngredientQuantity(metric=metric, us=us, as_entered=line),
            )
        )
    return ingredients


def _ingredient_name_and_notes(line: str, parsed: ParsedQuantity) -> tuple[str, str]:
    if parsed.unit == "to_taste":
        return line.strip(), ""
    candidate = _QUANTITY_PREFIX_RE.sub("", line, count=1).strip()
    candidate = _UNIT_PREFIX_RE.sub("", candidate, count=1).strip(" ;-:")
    candidate = candidate.lstrip(",").strip()
    name, _, notes = candidate.partition(",")
    name = name.strip()
    notes = notes.strip()
    if not name:
        raise ValueError(f"ingredient line has no name: {line}")
    return name, notes


def _steps(text: str) -> list[Step]:
    chunks = _non_empty_lines(text)
    return [
        Step(order=index, text=_STEP_NUMBER_RE.sub("", chunk).strip())
        for index, chunk in enumerate(chunks, 1)
    ]


def _photos(value: object, hero_caption: str = "") -> list[Photo]:
    if not isinstance(value, list):
        return []
    urls = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return [
        Photo(
            blob_url=url,
            caption=hero_caption if index == 0 else "",
            is_hero=index == 0,
        )
        for index, url in enumerate(urls)
    ]


def _csv_list(value: object) -> list[str]:
    if isinstance(value, str):
        raw_items = value.split(",")
    elif isinstance(value, list):
        raw_items = [item for item in value if isinstance(item, str)]
    else:
        raw_items = []
    return [item.strip() for item in raw_items if item.strip()]


def _lines_or_csv(value: object) -> list[str]:
    """Parse equipment-style fields that may be newline-OR-comma separated."""

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not isinstance(value, str):
        return []
    text = value.strip()
    if not text:
        return []
    parts = text.splitlines() if "\n" in text else text.split(",")
    return [part.strip(" -*•\t") for part in parts if part.strip(" -*•\t")]


def _non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _slugify(value: str) -> str:
    slug = _SLUG_RE.sub("-", value.lower()).strip("-")
    if not slug:
        raise ValueError("title must produce a slug")
    return slug


def _required_string(payload: dict[str, object], key: str) -> str:
    value = _string_value(payload.get(key))
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _string_value(value: object, *, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = value.strip()
        return text if text else default
    return str(value).strip()


def _int_value(value: object, *, default: int) -> int:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        raise ValueError("boolean values are not valid integers")
    if isinstance(value, int | float | str):
        return int(value)
    raise ValueError(f"expected an integer-compatible value, got {type(value).__name__}")


if __name__ == "__main__":
    raise SystemExit(main())
