from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from book.render import render_chapter, sort_recipes, typst_escape

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "book" / "fixtures" / "recipes.json"


def test_typst_escape_covers_special_characters() -> None:
    assert typst_escape(r"\*_#@<>[]$") == r"\\\*\_\#\@\<\>\[\]\$"


def test_render_chapter_fixture_recipe() -> None:
    recipe = json.loads(FIXTURES.read_text(encoding="utf-8"))[0]

    chapter = render_chapter(recipe)

    assert chapter.strip()
    assert "Chicken Adobo" in chapter
    assert "#recipe(" in chapter


def test_build_book_from_fixtures_end_to_end() -> None:
    output_dir = ROOT / "book" / "build" / "test-output"
    if output_dir.exists():
        shutil.rmtree(output_dir)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "book.build_book",
            "--from-fixtures",
            "--output",
            str(output_dir),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    book_typ = ROOT / "book" / "build" / "book.typ"
    assert book_typ.exists()
    rendered = book_typ.read_text(encoding="utf-8")
    for title in (
        "Chicken Adobo",
        "Pão de Queijo",
        "Lemon Caesar Salad",
        "Chocolate Olive Oil Cake",
        "Cucumber Mint Cooler",
    ):
        assert title in rendered or title in _rendered_chapter_sources()

    if shutil.which("typst") is None:
        assert result.returncode == 2
        assert "typst not found" in result.stderr
        return

    assert result.returncode == 0, result.stderr
    pdf = output_dir / "hls-cookbook-preview-en.pdf"
    assert pdf.exists()
    assert pdf.stat().st_size > 0


def test_sort_order_uses_canonical_courses_then_title() -> None:
    recipes = [
        _recipe("Z Drink", "drink"),
        _recipe("B Main", "main"),
        _recipe("A Main", "main"),
        _recipe("A Dessert", "dessert"),
        _recipe("A Appetizer", "appetizer"),
        _recipe("A Other", "brunch"),
        _recipe("A Side", "side"),
    ]

    assert [recipe["title"] for recipe in sort_recipes(recipes)] == [
        "A Appetizer",
        "A Main",
        "B Main",
        "A Side",
        "A Dessert",
        "Z Drink",
        "A Other",
    ]


def _recipe(title: str, course: str) -> dict[str, object]:
    return {
        "id": title,
        "title": title,
        "slug": title.lower().replace(" ", "-"),
        "classification": {"course": course},
    }


def _rendered_chapter_sources() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "book" / "chapters").glob("*/*.typ")
    )
