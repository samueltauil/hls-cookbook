# HLS Cookbook architecture

This document explains the git-native architecture for developers and curious
maintainers.

## Why git-native

Recipes are durable content, and GitHub already gives this project identity,
review, history, comments, notifications, and automation. Keeping recipes as YAML
in git means there is no service to run, no custom admin UI to maintain, and no
separate audit log to reconcile. The workflow scales with repository activity:
one issue becomes one PR, one merge updates the source of truth, and one build
publishes the cookbook.

## System diagram

```text
┌──────────────────────┐
│ GitHub Issue Form    │
│ "Submit a recipe"    │
└──────────┬───────────┘
           │ issue labeled recipe-submission
           ▼
┌──────────────────────┐
│ gh-aw workflow       │
│ normalize + photos   │
└──────────┬───────────┘
           │ create PR
           ▼
┌──────────────────────┐
│ Pull request         │
│ recipes/<slug>/...   │
└──────────┬───────────┘
           │ PR checks
           ▼
┌──────────────────────┐
│ CI validate          │
│ hls.validate         │
└──────────┬───────────┘
           │ merge
           ▼
┌──────────────────────┐
│ Cookbook build       │
│ Typst PDF / EPUB     │
└──────────┬───────────┘
           │ publish artifact
           ▼
┌──────────────────────┐
│ GitHub Release       │
│ cookbook files       │
└──────────────────────┘
```

## Components

- [`hls/`](../hls/) — pure-Python domain library: models, units, nutrition,
  normalization, validation, and repository loading.
- [`book/`](../book/) — Typst-based rendering pipeline for PDF output and
  optional EPUB generation.
- [`data/ingredients.yaml`](../data/ingredients.yaml) — canonical ingredient
  master with nutrition values and density data.
- [`recipes/`](../recipes/) — source-of-truth recipe YAML tree, one directory per
  recipe slug.
- [`.github/ISSUE_TEMPLATE/recipe.yml`](../.github/ISSUE_TEMPLATE/recipe.yml) —
  GitHub Issue Form for recipe submissions.
- [`.github/workflows/ingest-recipe.md`](../.github/workflows/ingest-recipe.md) —
  gh-aw agentic workflow that converts an issue into a recipe PR.
- [`.github/workflows/validate-recipes.yml`](../.github/workflows/validate-recipes.yml) —
  fast PR-time recipe validation.
- [`.github/workflows/build-cookbook.yml`](../.github/workflows/build-cookbook.yml) —
  cookbook build and release workflow.
- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) — repo-wide lint,
  test, and typecheck workflow.

## Recipe schema

The source of truth is [`hls/models/recipe.py`](../hls/models/recipe.py). The
issue payload accepted by the normalizer is documented in
[`hls/normalize.py`](../hls/normalize.py). Each default English recipe lives at
`recipes/<slug>/recipe.yaml`; locale variants live beside it as
`recipes/<slug>/recipe.<locale>.yaml`.

Top-level fields:

| Field | Type | Notes |
|---|---|---|
| `id` | string | Stable `rcp_` identifier shared by locale variants. |
| `slug` | string | Directory name and URL-safe identifier. |
| `locale` | string | BCP-47-ish language code; `en` is the default. |
| `title` | string | Printed recipe title. |
| `summary` | string | Short description or story shown above the recipe. |
| `status` | enum | `draft`, `in_review`, `approved`, or `rejected`. |
| `contributor` | object | `id`/GitHub handle and `display_name`. |
| `source` | object | Optional attribution and URL for adapted recipes. |
| `classification` | object | Cuisine, course, dietary tags, allergens, occasion, keywords, and difficulty. |
| `yield` | object | `servings` and optional `notes`. |
| `times` | object | `prep_min`, `cook_min`, `rest_min`, and `total_min`. |
| `ingredients` | list | Name, quantity, notes, and section for each ingredient. |
| `steps` | list | Ordered cooking instructions. |
| `equipment` | list | Tools useful for making the recipe. |
| `tips` | string | Substitutions, cook cues, and contributor advice. |
| `storage` | string | Leftover, make-ahead, freezer, and reheating guidance. |
| `pairings` | string | Serving suggestions, sides, drinks, and garnishes. |
| `photos` | list | Relative photo path, caption, and hero flag. |
| `nutrition_per_serving` | object | Calories, protein, fat, and carbs per serving. |
| `review` | object | Review timestamps, reviewer, and notes. |
| `book` | object | Edition inclusion metadata. |
| `created_at` / `updated_at` | datetime | Audit timestamps. |
| `_etag` | string or null | Legacy-compatible field; normally null in git. |

Ingredient sections come from `## Section` headings in the issue form. Text after
a trailing comma is preserved in `Ingredient.notes`, so `2 lb chicken thighs,
bone-in, skin-on` becomes name `chicken thighs` with notes `bone-in, skin-on`.

Complete example:

```yaml
id: rcp_01HXYZABCDEF0123456789ABCD
slug: chicken-adobo
locale: en
title: Chicken Adobo
summary: A bone-in Filipino braise where soy sauce, vinegar, garlic, and bay leaves transform humble chicken into something deeply savory and tangy.
status: approved
contributor: { id: samueltauil, display_name: Sam Tauil }
source: { attribution: "Adapted from Sam's family recipe", url: "" }
classification:
  cuisine: Filipino
  course: main
  dietary_tags: [dairy-free, gluten-free]
  allergens: [soy]
  occasion: [weeknight, batch-cook]
  keywords: [one-pot, comfort food, freezer-friendly]
  difficulty: easy
yield: { servings: 4, notes: "Halve for snack portions" }
times: { prep_min: 15, cook_min: 45, rest_min: 30, total_min: 90 }
ingredients:
  - section: marinade
    name: soy sauce
    notes: low-sodium preferred
    quantity:
      as_entered: "1/4 cup soy sauce, low-sodium preferred"
      metric: { value: 60, unit: ml }
      us: { value: 0.25, unit: cup }
  - section: braise
    name: chicken thighs
    notes: bone-in, skin-on
    quantity:
      as_entered: "2 lb chicken thighs, bone-in, skin-on"
      metric: { value: 900, unit: g }
      us: { value: 2, unit: lb }
steps:
  - { order: 1, text: "Marinate chicken in soy and vinegar for 30 min." }
  - { order: 2, text: "Brown the chicken in oil over medium-high heat." }
equipment: ["Heavy-bottomed pot or Dutch oven", "Tongs"]
tips: "Cane vinegar (sukang iloko) is traditional; cider vinegar works."
storage: "Keeps 4 days refrigerated; freezes 3 months."
pairings: "Steamed jasmine rice and pickled green papaya."
photos:
  - { blob_url: photos/hero.jpg, caption: "Adobo over jasmine rice", is_hero: true }
nutrition_per_serving: { calories_kcal: 410, protein_g: 32, fat_g: 22, carbs_g: 14 }
review: { submitted_at: null, reviewer_id: null, review_notes: [] }
book: { included_in_editions: [] }
created_at: "2026-06-12T00:00:00Z"
updated_at: "2026-06-12T00:00:00Z"
_etag: null
```

## i18n / locale variants

The default locale is `en`, and default recipe files are stored at
`recipes/<slug>/recipe.yaml`. Other locales are stored next to the default file as
`recipes/<slug>/recipe.<locale>.yaml`, for example
[`recipes/pao-de-queijo/recipe.pt-BR.yaml`](../recipes/pao-de-queijo/recipe.pt-BR.yaml).

The book build selects a language with `--locale <code>`, such as:

```bash
python -m book.build_book --locale pt-BR --edition preview
```

Locale variants should share the same `id`, `slug`, `contributor`,
classification, quantities, and nutrition. Only narrative fields need
translation: `title`, `summary`, `steps`, `tips`, `storage`, `pairings`, photo
captions, and similar reader-facing text.

## Ingredient master schema

The source of truth is [`hls/models/ingredient_master.py`](../hls/models/ingredient_master.py).
The file [`data/ingredients.yaml`](../data/ingredients.yaml) stores a top-level
`ingredients` list.

| Field | Type | Notes |
|---|---|---|
| `canonical_name` | string | Stable lower_snake_case key. |
| `display_name` | string | Human-readable ingredient name. |
| `aliases` | list[string] | Natural names matched during normalization. |
| `density_g_per_ml` | number or null | Used for volume-to-mass conversion. |
| `nutrition_per_100g` | object or null | Calories, protein, fat, and carbs per 100 g. |

Example:

```yaml
ingredients:
  - canonical_name: brown_sugar
    display_name: brown sugar
    aliases:
      - brown sugar
      - light brown sugar
    density_g_per_ml: 0.72
    nutrition_per_100g:
      calories_kcal: 380
      protein_g: 0.1
      fat_g: 0
      carbs_g: 98.1
```

## Unit handling

Recipes store both metric and US-friendly quantities, plus the original
`as_entered` text. `hls.units` uses Pint-based parsing for common masses,
volumes, counts, ranges, fractions, and `to taste`. When a conversion crosses
volume and mass, the converter asks the ingredient master for `density_g_per_ml`.
If density is unknown, validation can still pass, but the PR should show what
could not be normalized.

## Nutrition aggregation

`compute_recipe_nutrition` walks each ingredient, converts the amount to grams,
looks up `nutrition_per_100g`, multiplies by ingredient mass, sums the totals,
and divides by `yield.servings`. Ingredients without enough data are skipped
rather than blocking the recipe.

## Photo handling

The issue form accepts pasted URLs and drag-and-drop attachments. The ingestion
agent downloads each photo, commits it under `recipes/<slug>/photos/`, and writes
relative paths into the recipe. During the book build, photos are copied into
`book/assets/photos/` so Typst can include them in the generated pages.

## Editions

`book.included_in_editions` lists named cookbook editions that should include the
recipe. `book.build_book --edition preview` includes every approved recipe.
Named builds, such as `--edition 2026-fall`, include approved recipes whose book
metadata contains that edition.

## Why we dropped FastAPI/Cosmos

An earlier iteration used a FastAPI service and Cosmos DB. The project pivoted
because recipes are reviewable content, not high-traffic transactions.
Git-native storage removes operational overhead, uses familiar PR review, keeps
history in one place, and still gives contributors a simple issue-form UX.

The richer schema we ship today — sections, allergens, source attribution,
equipment, i18n variants, and more — would have been a real chore in a Cosmos
document. In git, it is just YAML diffs maintainers can read at a glance.
