"""Render approved recipes into Typst source."""

from __future__ import annotations

import re
from collections import OrderedDict
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any, NotRequired, TypedDict, cast

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape


class FixtureRecipe(TypedDict, total=False):
    id: str
    title: str
    slug: str
    status: str
    summary: str
    contributor: dict[str, Any]
    classification: dict[str, Any]
    yield_: NotRequired[dict[str, Any]]
    times: dict[str, Any]
    ingredients: list[dict[str, Any]]
    steps: list[dict[str, Any] | str]
    photos: list[dict[str, Any]]
    nutrition_per_serving: dict[str, Any] | None
    locales: dict[str, Any]


RecipeLike = FixtureRecipe | Mapping[str, Any] | Any

BOOK_DIR = Path(__file__).resolve().parent
COURSE_ORDER = ("appetizer", "main", "side", "dessert", "drink", "other")
COURSE_LABELS = {
    "appetizer": "Appetizers",
    "main": "Mains",
    "side": "Sides",
    "dessert": "Desserts",
    "drink": "Drinks",
    "other": "Other",
}
SPECIAL_CHARS = {
    "\\": "\\\\",
    "*": "\\*",
    "_": "\\_",
    "#": "\\#",
    "@": "\\@",
    "<": "\\<",
    ">": "\\>",
    "[": "\\[",
    "]": "\\]",
    "$": "\\$",
}


def typst_escape(value: object) -> str:
    """Escape user-supplied text for Typst markup content blocks."""
    text = "" if value is None else str(value)
    return "".join(SPECIAL_CHARS.get(char, char) for char in text)


def typst_string(value: object) -> str:
    """Render a Typst string literal for controlled values such as file paths."""
    text = "" if value is None else str(value)
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def slugify(value: object) -> str:
    """Create a filesystem-safe slug."""
    text = str(value or "").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return slug or "recipe"


def get_jinja_env() -> Environment:
    """Create the Jinja environment used for Typst generation."""
    env = Environment(
        loader=FileSystemLoader(BOOK_DIR),
        autoescape=select_autoescape(default=False),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["typst_escape"] = typst_escape
    env.filters["typst_path"] = _typst_path
    env.filters["typst_content_or_none"] = _typst_content_or_none
    return env


def sort_recipes(recipes: Sequence[RecipeLike]) -> list[RecipeLike]:
    """Sort recipes in printed-book order."""
    order = {course: index for index, course in enumerate(COURSE_ORDER)}
    return sorted(
        recipes,
        key=lambda recipe: (
            order.get(_course_key(recipe), order["other"]),
            _string_field(recipe, "title").casefold(),
        ),
    )


def chapter_path(recipe: RecipeLike) -> Path:
    """Return the generated chapter path relative to the book directory."""
    data = _as_mapping(recipe)
    course = _course_key(data)
    slug = slugify(data.get("slug") or data.get("title") or data.get("id"))
    return Path("chapters") / course / f"{slug}.typ"


def chapter_include_path(recipe: RecipeLike) -> str:
    """Return the include path from book/build/book.typ."""
    return f"../{chapter_path(recipe).as_posix()}"


def render_chapter(recipe: RecipeLike) -> str:
    """Render a recipe chapter as Typst source."""
    context = _recipe_context(recipe)
    return get_jinja_env().get_template("chapter.typ.j2").render(recipe=context)


def render_book(recipes: Sequence[RecipeLike], edition: str, locale: str) -> str:
    """Render the top-level Typst book file."""
    sorted_recipes = sort_recipes(recipes)
    lines = [
        '#import "../template.typ": cookbook, cover, front-matter, contents, chapter-divider',
        "",
        "#show: cookbook",
        "",
        f"#cover(edition: {typst_string(edition)}, date: {typst_string(_display_date())})",
        "#front-matter()",
        "#contents()",
        "",
    ]
    previous_course = ""
    for recipe in sorted_recipes:
        course = _course_key(recipe)
        if course != previous_course:
            lines.append(f"#chapter-divider([{typst_escape(COURSE_LABELS.get(course, 'Other'))}])")
            previous_course = course
        lines.append(f'#include "{chapter_include_path(recipe)}"')
        lines.append("")

    return "\n".join(lines)


def render_markdown(recipes: Sequence[RecipeLike], edition: str, locale: str) -> str:
    """Render a simple Markdown edition for optional EPUB conversion."""
    lines = [
        "% HLS Cookbook",
        "% Hot Lunch Society",
        f"% {_display_date()}",
        "",
        f"# HLS Cookbook — {edition} ({locale})",
        "",
        "A collection from the Hot Lunch Society.",
        "",
    ]
    previous_course = ""
    for recipe in sort_recipes(recipes):
        context = _recipe_context(recipe)
        if context["course"] != previous_course:
            lines.extend([f"## {context['course_label']}", ""])
            previous_course = str(context["course"])
        lines.extend(
            [
                f"### {context['title']}",
                "",
                str(context["summary"]),
                "",
                f"**Contributor:** {context['contributor']}  ",
                f"**Servings:** {context['servings']}",
                "",
                "#### Ingredients",
                "",
            ],
        )
        for section in cast(list[dict[str, Any]], context["ingredient_sections"]):
            title = section["title"]
            if title:
                lines.extend([f"**{title}**", ""])
            for item in cast(list[dict[str, str | None]], section["items"]):
                quantity = f"{item['quantity']} " if item["quantity"] else ""
                notes = f", {item['notes']}" if item["notes"] else ""
                lines.append(f"- {quantity}{item['name']}{notes}")
            lines.append("")
        lines.extend(["#### Steps", ""])
        for index, step in enumerate(cast(list[str], context["steps"]), start=1):
            lines.append(f"{index}. {step}")
        lines.append("")
    return "\n".join(lines)


def _as_mapping(recipe: RecipeLike) -> Mapping[str, Any]:
    if isinstance(recipe, Mapping):
        return recipe
    model_dump = getattr(recipe, "model_dump", None)
    if callable(model_dump):
        return cast(Mapping[str, Any], model_dump(mode="json", by_alias=True))
    return cast(Mapping[str, Any], vars(recipe))


def _recipe_context(recipe: RecipeLike) -> dict[str, Any]:
    data = _as_mapping(recipe)
    locale = str(data.get("_locale") or "en")
    title = _localized_field(data, "title", locale) or _string_field(data, "title")
    summary = _localized_field(data, "summary", locale) or _string_field(data, "summary")
    nutrition = _nutrition(data.get("nutrition_per_serving"))
    return {
        "title": title,
        "hero_photo": _hero_photo_path(data),
        "contributor": _contributor(data),
        "course": _course_key(data),
        "course_label": COURSE_LABELS.get(_course_key(data), "Other"),
        "dietary_tags": _dietary_tags(data),
        "prep_time": _minutes(data, "prep_min"),
        "cook_time": _minutes(data, "cook_min"),
        "total_time": _minutes(data, "total_min"),
        "servings": _servings(data),
        "summary": summary,
        "ingredient_sections": _ingredient_sections(data),
        "steps": _steps(data, locale),
        "nutrition_complete": nutrition["complete"],
        "nutrition": nutrition,
    }


def _localized_field(data: Mapping[str, Any], field: str, locale: str) -> str:
    locales = data.get("locales")
    if not isinstance(locales, Mapping):
        return ""
    localized = locales.get(locale)
    if not isinstance(localized, Mapping):
        return ""
    value = localized.get(field)
    return str(value) if value else ""


def _string_field(recipe: RecipeLike, field: str) -> str:
    value = _as_mapping(recipe).get(field)
    return str(value or "")


def _nested_text(data: Mapping[str, Any], *keys: str) -> str:
    value: Any = data
    for key in keys:
        if not isinstance(value, Mapping):
            return ""
        value = value.get(key)
    return str(value) if value is not None else ""


def _course_key(recipe: RecipeLike) -> str:
    course = _nested_text(_as_mapping(recipe), "classification", "course").lower()
    return course if course in COURSE_ORDER else "other"


def _contributor(data: Mapping[str, Any]) -> str:
    contributor = data.get("contributor")
    if isinstance(contributor, Mapping):
        return str(contributor.get("display_name") or contributor.get("id") or "—")
    return "—"


def _dietary_tags(data: Mapping[str, Any]) -> str:
    tags = data.get("classification")
    if not isinstance(tags, Mapping):
        return "—"
    value = tags.get("dietary_tags")
    if isinstance(value, Sequence) and not isinstance(value, str):
        return ", ".join(str(tag) for tag in value) or "—"
    return str(value or "—")


def _minutes(data: Mapping[str, Any], key: str) -> str:
    times = data.get("times")
    if not isinstance(times, Mapping):
        return "—"
    value = times.get(key)
    if value in (None, ""):
        return "—"
    return f"{value} min"


def _servings(data: Mapping[str, Any]) -> str:
    yield_data = data.get("yield")
    if not isinstance(yield_data, Mapping):
        yield_data = data.get("yield_")
    if not isinstance(yield_data, Mapping):
        return "—"
    servings = yield_data.get("servings")
    notes = yield_data.get("notes")
    if servings and notes:
        return f"{servings} ({notes})"
    return str(servings or "—")


def _ingredient_sections(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    ingredients = data.get("ingredients")
    if not isinstance(ingredients, Sequence) or isinstance(ingredients, str):
        return []
    grouped: OrderedDict[str, list[dict[str, str | None]]] = OrderedDict()
    for ingredient in ingredients:
        if not isinstance(ingredient, Mapping):
            continue
        section = str(ingredient.get("section") or "")
        grouped.setdefault(section, []).append(
            {
                "quantity": _quantity_text(ingredient.get("quantity")),
                "name": str(ingredient.get("name") or ""),
                "notes": str(ingredient.get("notes") or "") or None,
            },
        )
    titled_sections = [section for section in grouped if section]
    show_titles = len(titled_sections) > 1
    return [
        {
            "title": _section_title(section) if show_titles and section else None,
            "items": items,
        }
        for section, items in grouped.items()
    ]


def _section_title(section: str) -> str:
    return section.replace("-", " ").replace("_", " ").title()


def _quantity_text(quantity: Any) -> str | None:
    if not isinstance(quantity, Mapping):
        return None
    metric = _unit_amount(quantity.get("metric"))
    us = _unit_amount(quantity.get("us"))
    as_entered = str(quantity.get("as_entered") or "")
    if metric and us and metric != us:
        return f"{metric} ({us})"
    return metric or us or as_entered or None


def _unit_amount(value: Any) -> str:
    if not isinstance(value, Mapping):
        return ""
    amount = value.get("value")
    unit = value.get("unit")
    if amount in (None, "") and not unit:
        return ""
    return " ".join(part for part in (_format_amount(amount), str(unit or "")) if part)


def _format_amount(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _steps(data: Mapping[str, Any], locale: str) -> list[str]:
    localized_steps = _localized_steps(data, locale)
    if localized_steps:
        return localized_steps

    steps = data.get("steps")
    if not isinstance(steps, Sequence) or isinstance(steps, str):
        return []
    normalized: list[tuple[int, str]] = []
    for index, step in enumerate(steps, start=1):
        if isinstance(step, Mapping):
            order = step.get("order")
            normalized.append(
                (int(order) if isinstance(order, int) else index, str(step.get("text") or ""))
            )
        else:
            normalized.append((index, str(step)))
    return [text for _, text in sorted(normalized, key=lambda item: item[0]) if text]


def _localized_steps(data: Mapping[str, Any], locale: str) -> list[str]:
    locales = data.get("locales")
    if not isinstance(locales, Mapping):
        return []
    localized = locales.get(locale)
    if not isinstance(localized, Mapping):
        return []
    steps = localized.get("steps")
    if not isinstance(steps, Sequence) or isinstance(steps, str):
        return []
    return [str(step.get("text") if isinstance(step, Mapping) else step) for step in steps]


def _nutrition(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return _empty_nutrition()
    fields = {
        "calories": ("calories_kcal", "kcal"),
        "protein": ("protein_g", "g"),
        "fat": ("fat_g", "g"),
        "carbs": ("carbs_g", "g"),
    }
    missing = [source for source, _ in fields.values() if value.get(source) in (None, "")]
    if missing:
        return _empty_nutrition()
    return {
        "complete": True,
        **{
            target: f"{_format_amount(value[source])} {unit}"
            for target, (source, unit) in fields.items()
        },
    }


def _empty_nutrition() -> dict[str, Any]:
    return {"complete": False, "calories": "—", "protein": "—", "fat": "—", "carbs": "—"}


def _typst_path(value: object) -> str:
    if not value:
        return "none"
    return typst_string(value)


def _hero_photo_path(data: Mapping[str, Any]) -> str | None:
    raw_path = data.get("_hero_photo_path")
    if not raw_path:
        return None

    path = Path(str(raw_path))
    if path.is_absolute():
        try:
            return path.relative_to(BOOK_DIR).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix()


def _typst_content_or_none(value: object) -> str:
    if value in (None, ""):
        return "none"
    return f"[{typst_escape(value)}]"


def _display_date() -> str:
    return date.today().strftime("%B %-d, %Y")
