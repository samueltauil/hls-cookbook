# HLS Cookbook — Hot Lunch Society

An internal Microsoft cookbook that turns recipe issues into a printable book.

[![Submit a recipe](https://img.shields.io/badge/%F0%9F%8D%B3%20Submit%20a%20recipe-2ea44f?style=for-the-badge)](https://github.com/samueltauil/hls-cookbook/issues/new?template=recipe.yml)

## What this is

HLS Cookbook is an internal Microsoft project for collecting recipes from the
Hot Lunch Society and publishing them as a printed cookbook automatically. Cooks
submit recipes with a GitHub Issue Form, an agentic workflow turns each
submission into versioned YAML, maintainers review the generated pull request,
and the cookbook PDF rebuilds from the merged recipe files.

## How it works

- 📝 Open an issue using the **Submit a recipe** template.
- 🤖 An agentic workflow normalizes the recipe and opens a PR.
- ✅ Maintainers review the PR; CI validates the YAML.
- 📖 On merge, the cookbook PDF auto-rebuilds.

## Quick links

- [Submit a recipe](https://github.com/samueltauil/hls-cookbook/issues/new?template=recipe.yml)
- [Contributing guide](./CONTRIBUTING.md)
- [Recipe submission guide](./docs/recipe-submission-guide.md)
- [Architecture doc](./docs/architecture.md)
- Latest cookbook downloads (rebuilt automatically from `main`):
  - [📕 PDF · English](https://github.com/samueltauil/hls-cookbook/releases/download/cookbook-latest/hls-cookbook-preview-en.pdf)
  - [📘 EPUB · English](https://github.com/samueltauil/hls-cookbook/releases/download/cookbook-latest/hls-cookbook-preview-en.epub)
  - [All builds](https://github.com/samueltauil/hls-cookbook/releases)

> The build ships English only for now. The repo already has i18n
> scaffolding (locale-suffixed YAMLs, e.g. `recipe.pt-BR.yaml`) but
> translation/localization is on the roadmap and not part of the
> automated release yet.

## Local development

Required tools:

- Python 3.12
- [Typst](https://typst.app/) for PDF builds
- Optional: [Pandoc](https://pandoc.org/) for EPUB builds

```bash
git clone https://github.com/samueltauil/hls-cookbook.git
cd hls-cookbook
python3.12 -m venv .venv
. .venv/bin/activate
make install
make test
make book
make validate
```

Common targets:

```bash
make install    # install runtime and dev dependencies into the active venv
make test       # run pytest
make lint       # run ruff checks
make format     # format with ruff
make typecheck  # run mypy
make validate   # validate every recipe under recipes/
make book       # build the cookbook PDF into dist/
make book-fixtures # build from bundled fixture recipes
make clean      # remove generated artifacts and caches
```

The Python entry points are also available directly:

```bash
python -m hls.normalize --issue-json issue.json
python -m hls.validate recipes/
hls validate recipes/   # if the console script is installed
```

## Repo layout

```text
hls-cookbook/
├── hls/          Pure-Python domain library: models, units, nutrition, normalize, validate
├── book/         Typst templates and cookbook rendering pipeline
├── data/         Canonical ingredient master with nutrition and density data
├── recipes/      Source-of-truth recipe YAML, one directory per recipe slug
├── tests/        pytest coverage for models, units, normalization, validation, and book output
├── docs/         User, contributor, and architecture documentation
├── .github/      Issue forms and GitHub Actions workflows
├── Makefile      Local development commands
└── pyproject.toml Project metadata, dependencies, and tool configuration
```

## For recipe contributors

Start with the [recipe submission guide](./docs/recipe-submission-guide.md). You
can write ingredients naturally, attach photos in the issue, and watch the agent
open a PR for review.

## For maintainers and developers

Read [CONTRIBUTING.md](./CONTRIBUTING.md) for schema notes, validation rules,
agentic workflow updates, and local development commands. The deeper system
reference is in [docs/architecture.md](./docs/architecture.md).

Before opening a PR, run the checks that match your change:

- Recipe-only changes: `make validate`
- Python changes: `make test`, `make lint`, and `make typecheck`
- Book changes: `make book` or `make book-fixtures`

## License

MIT. See the license declaration in [`pyproject.toml`](./pyproject.toml).
