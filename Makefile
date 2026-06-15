.PHONY: help install dev test lint format typecheck validate book book-fixtures clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime + dev dependencies into the current venv
	pip install --upgrade pip
	pip install -e ".[dev]"

dev: install ## Alias for install

test: ## Run pytest
	pytest

lint: ## Run ruff
	ruff check .
	ruff format --check .

format: ## Auto-format with ruff
	ruff format .
	ruff check --fix .

typecheck: ## Run mypy
	mypy hls book

validate: ## Validate every recipe under recipes/ against the schema
	python -m hls.validate recipes/

book: ## Generate the cookbook PDF from recipes/ on disk
	python -m book.build_book --output dist/

book-fixtures: ## Build a sample PDF from book/fixtures/ (no recipes/ tree needed)
	python -m book.build_book --from-fixtures --output dist/

clean: ## Remove build artifacts and caches
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
