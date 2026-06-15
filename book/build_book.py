"""CLI orchestration for the printed HLS Cookbook build."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from book.render import (
    RecipeLike,
    chapter_path,
    render_book,
    render_chapter,
    render_markdown,
    slugify,
    sort_recipes,
    typst_string,
)
from book.repo_source import load_recipes as load_repo_recipes

BOOK_DIR = Path(__file__).resolve().parent
FIXTURES_PATH = BOOK_DIR / "fixtures" / "recipes.json"
BUILD_DIR = BOOK_DIR / "build"
CHAPTERS_DIR = BOOK_DIR / "chapters"
PHOTOS_DIR = BOOK_DIR / "assets" / "photos"


class BuildError(RuntimeError):
    """Clear build failure with a process exit code."""

    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


def main(argv: Sequence[str] | None = None) -> int:
    """Run the cookbook build CLI."""
    parser = argparse.ArgumentParser(description="Build the printed HLS Cookbook.")
    parser.add_argument("--edition", default="preview", help="Cookbook edition name.")
    parser.add_argument("--locale", default="en", choices=("en", "pt-BR"), help="Render locale.")
    parser.add_argument("--output", default="dist/", help="Output directory for PDF/EPUB.")
    parser.add_argument(
        "--from-fixtures",
        action="store_true",
        help="Use book/fixtures/recipes.json instead of recipes/*/recipe.yaml.",
    )
    args = parser.parse_args(argv)

    try:
        build_book(
            edition=args.edition,
            locale=args.locale,
            output_dir=Path(args.output),
            from_fixtures=args.from_fixtures,
        )
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.code
    return 0


def build_book(
    *,
    edition: str,
    locale: str,
    output_dir: Path,
    from_fixtures: bool,
) -> Path:
    """Build Typst sources, compile PDF, and optionally emit EPUB."""
    recipes = _load_recipes(edition=edition, locale=locale, from_fixtures=from_fixtures)
    if not recipes:
        raise BuildError("No approved recipes were found for the requested cookbook.")

    prepared = _prepare_recipes(recipes, locale=locale, skip_photos=from_fixtures)
    _write_chapters(prepared)
    book_typ = _write_book(prepared, edition=edition, locale=locale)
    book_md = _write_markdown(prepared, edition=edition, locale=locale)

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"hls-cookbook-{slugify(edition)}-{locale}.pdf"
    pdf_path = output_dir / filename
    _compile_typst(book_typ, pdf_path)
    _compile_epub(book_md, output_dir / filename.replace(".pdf", ".epub"))
    print(f"Built {pdf_path}")
    return pdf_path


def _load_recipes(*, edition: str, locale: str, from_fixtures: bool) -> list[RecipeLike]:
    if from_fixtures:
        data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
        return [_with_locale(cast(dict[str, Any], recipe), locale) for recipe in data]

    return [
        _with_locale(_as_dict(recipe), locale)
        for recipe in load_repo_recipes(edition=edition, locale=locale)
    ]


def _prepare_recipes(
    recipes: Sequence[RecipeLike],
    *,
    locale: str,
    skip_photos: bool,
) -> list[RecipeLike]:
    prepared: list[RecipeLike] = []
    if not skip_photos:
        _clear_generated_photos()
    for recipe in sort_recipes(recipes):
        data = _with_locale(_as_dict(recipe), locale)
        if not skip_photos:
            photo = _copy_hero_photo(data)
            if photo is not None:
                data["_hero_photo_path"] = photo.relative_to(BOOK_DIR).as_posix()
        prepared.append(data)
    return prepared


def _write_chapters(recipes: Sequence[RecipeLike]) -> None:
    _clear_generated_chapters()
    for recipe in recipes:
        path = BOOK_DIR / chapter_path(recipe)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_chapter(recipe), encoding="utf-8")


def _write_book(recipes: Sequence[RecipeLike], *, edition: str, locale: str) -> Path:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    book_typ = BUILD_DIR / "book.typ"
    book_typ.write_text(render_book(recipes, edition=edition, locale=locale), encoding="utf-8")
    return book_typ


def _write_markdown(recipes: Sequence[RecipeLike], *, edition: str, locale: str) -> Path:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    book_md = BUILD_DIR / "book.md"
    book_md.write_text(render_markdown(recipes, edition=edition, locale=locale), encoding="utf-8")
    return book_md


def _compile_typst(book_typ: Path, pdf_path: Path) -> None:
    typst = shutil.which("typst")
    if typst is None:
        raise BuildError(
            "typst not found on PATH; generated Typst sources under book/build/ but skipped PDF.",
            code=2,
        )

    result = subprocess.run(
        [typst, "compile", "--root", str(BOOK_DIR), str(book_typ), str(pdf_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise BuildError("typst compile failed.", code=result.returncode)


def _compile_epub(book_md: Path, epub_path: Path) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        return
    result = subprocess.run(
        [pandoc, str(book_md), "-o", str(epub_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 and result.stderr:
        print(f"warning: pandoc EPUB generation failed: {result.stderr}", file=sys.stderr)


def _clear_generated_chapters() -> None:
    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)
    for path in CHAPTERS_DIR.glob("*/*.typ"):
        path.unlink()


def _clear_generated_photos() -> None:
    if PHOTOS_DIR.exists():
        shutil.rmtree(PHOTOS_DIR)
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)


def _copy_hero_photo(recipe: Mapping[str, Any]) -> Path | None:
    photo = _hero_photo(recipe)
    if photo is None:
        return None

    raw_file = photo.get("file") or photo.get("blob_url")
    if not raw_file:
        return None

    slug = slugify(recipe.get("slug") or recipe.get("title") or recipe.get("id"))
    source = _photo_source_path(slug=slug, raw_file=str(raw_file))
    if source is None or not source.exists():
        return None

    destination = PHOTOS_DIR / slug / source.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    if not _typst_can_decode_image(destination.relative_to(BOOK_DIR).as_posix()):
        destination.unlink(missing_ok=True)
        print(f"warning: skipping undecodable hero photo for {slug}: {source}", file=sys.stderr)
        return None
    return destination


def _hero_photo(recipe: Mapping[str, Any]) -> Mapping[str, Any] | None:
    photos = recipe.get("photos")
    if not isinstance(photos, Sequence) or isinstance(photos, str):
        return None

    first_photo: Mapping[str, Any] | None = None
    for photo in photos:
        if not isinstance(photo, Mapping):
            continue
        first_photo = first_photo or photo
        if photo.get("is_hero"):
            return photo
    return first_photo


def _photo_source_path(*, slug: str, raw_file: str) -> Path | None:
    relative = Path(raw_file)
    if relative.is_absolute() or ".." in relative.parts:
        raise BuildError(f"Unsafe photo path for {slug}: {raw_file}")

    recipe_dir = Path(__file__).resolve().parents[1] / "recipes" / slug
    candidates = [recipe_dir / relative]
    if relative.parts[:1] != ("photos",):
        candidates.append(recipe_dir / "photos" / relative)
    return next((candidate for candidate in candidates if candidate.exists()), candidates[-1])


def _typst_can_decode_image(relative_path: str) -> bool:
    typst = shutil.which("typst")
    if typst is None:
        return True

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    check_name = slugify(f"image-check-{relative_path}")
    check_typ = BUILD_DIR / f".{check_name}.typ"
    check_pdf = BUILD_DIR / f".{check_name}.pdf"
    try:
        check_typ.write_text(f"#image({typst_string(f'../{relative_path}')})\n", encoding="utf-8")
        result = subprocess.run(
            [typst, "compile", "--root", str(BOOK_DIR), str(check_typ), str(check_pdf)],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    finally:
        check_typ.unlink(missing_ok=True)
        check_pdf.unlink(missing_ok=True)


def _with_locale(recipe: dict[str, Any], locale: str) -> dict[str, Any]:
    recipe["_locale"] = locale
    return recipe


def _as_dict(recipe: RecipeLike) -> dict[str, Any]:
    if isinstance(recipe, dict):
        return dict(recipe)
    if isinstance(recipe, Mapping):
        return dict(recipe)
    model_dump = getattr(recipe, "model_dump", None)
    if callable(model_dump):
        return cast(dict[str, Any], model_dump(mode="json", by_alias=True))
    return dict(vars(recipe))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
