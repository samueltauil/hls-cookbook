# Contributing to HLS Cookbook

Thanks for cooking with the Hot Lunch Society. This guide covers recipe
submitters, maintainers, and developers working on the git-native cookbook flow.

## Three ways to contribute

### 1. Submit a recipe

Use the [Submit a recipe issue form](https://github.com/samueltauil/hls-cookbook/issues/new?template=recipe.yml).
Write the recipe as you would explain it to another cook; the ingestion workflow
will normalize measurements, ingredients, photos, and metadata into a PR.

For a full walkthrough, see the
[recipe submission guide](./docs/recipe-submission-guide.md).

### 2. Improve the canonical ingredients

Open a PR against [`data/ingredients.yaml`](./data/ingredients.yaml) when an
ingredient is missing, has a better alias, needs density data, or needs updated
nutrition values. Keep canonical names stable and lower_snake_case.

### 3. Improve the codebase

Open a PR for changes under [`hls/`](./hls/), [`book/`](./book/),
[`tests/`](./tests/), [`docs/`](./docs/), or workflow files. Keep changes focused
and include validation evidence in the PR description.

## Recipe schema

The source of truth is [`hls/models/recipe.py`](./hls/models/recipe.py). A recipe
lives at `recipes/<slug>/recipe.yaml` and includes these top-level fields:

| Field | Purpose |
|---|---|
| `id` | Stable recipe identifier, generated with an `rcp_` prefix. |
| `status` | Review state: `draft`, `in_review`, `approved`, or `rejected`. |
| `title` / `slug` / `summary` | Display name, directory-safe slug, and short description. |
| `contributor` | Contributor id or GitHub handle plus display name. |
| `classification` | Course, dietary tags, difficulty, and occasions. |
| `yield` | Servings and optional yield notes. |
| `times` | Prep, cook, and total minutes. |
| `ingredients` | Ingredient names, quantities, notes, and sections. |
| `steps` | Ordered method text. |
| `photos` | Relative photo paths, captions, and hero flag. |
| `nutrition_per_serving` | Computed calories, protein, fat, and carbs. |
| `locales` | Optional localized title, summary, and steps. |
| `review` | Review metadata and notes. |
| `book` | Cookbook edition metadata. |
| `created_at` / `updated_at` | Audit timestamps. |

See [docs/architecture.md](./docs/architecture.md#recipe-schema) for a complete
example.

## Local development

Use a virtual environment for all Python commands:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
make install
```

Useful targets:

```bash
make test        # pytest
make lint        # ruff check + format check
make format      # ruff format + safe fixes
make typecheck   # mypy hls book
make validate    # python -m hls.validate recipes/
make book        # build the cookbook PDF into dist/
make clean       # remove generated artifacts and caches
```

Tests live in [`tests/`](./tests/) and should cover domain behavior, recipe
validation, normalization, and book rendering changes.

## Validation rules

`python -m hls.validate` checks recipe YAML before it can be merged:

- YAML parses cleanly.
- The document validates against `hls.models.Recipe`.
- The file is named `recipe.yaml`.
- The parent directory matches the recipe `slug`.
- No duplicate slug exists under `recipes/`.
- Ingredient names are checked against `data/ingredients.yaml`.
- Unrecognized ingredients are reported as warnings so maintainers can decide
  whether to add them to the master list.

Run the same check with:

```bash
python -m hls.validate recipes/
# or
hls validate recipes/
```

## Updating agentic workflows

Agentic workflows are authored in `.github/workflows/*.md` with YAML
frontmatter and compiled by the [`gh-aw`](https://github.com/github/gh-aw) CLI
extension. Install or update the extension, then compile before pushing:

```bash
gh extension install github/gh-aw
gh extension upgrade github/gh-aw
gh aw compile .github/workflows/ingest-recipe.md
```

Commit both the `.md` workflow source and the generated `.lock.yml` file.
Markdown-body-only edits do not require recompilation.

## Commit conventions

Use clear, descriptive commits. Conventional Commits are welcome
(`docs: rewrite recipe guide`, `fix: validate duplicate slugs`), but not required.
Keep each PR focused on one recipe, one data update, or one code/documentation
change.

## License agreement

By contributing recipes, ingredient data, documentation, or code, you agree that
your contribution is released under the same MIT license as this repository.
