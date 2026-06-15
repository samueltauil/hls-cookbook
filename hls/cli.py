"""HLS Cookbook command-line interface."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from hls import __version__
from hls.normalize import main as normalize_main
from hls.repo_source import load_recipes
from hls.validate import main as validate_main


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``hls`` console script."""

    parser = argparse.ArgumentParser(prog="hls")
    parser.add_argument("--version", action="version", version=f"hls {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    normalize_parser = subparsers.add_parser("normalize", help="Normalize an issue payload.")
    normalize_parser.add_argument("args", nargs=argparse.REMAINDER)

    validate_parser = subparsers.add_parser("validate", help="Validate recipe YAML.")
    validate_parser.add_argument("args", nargs=argparse.REMAINDER)

    subparsers.add_parser("list-recipes", help="List recipe slugs and titles.")

    args = parser.parse_args(argv)
    if args.command == "normalize":
        return normalize_main(args.args)
    if args.command == "validate":
        return validate_main(args.args)
    if args.command == "list-recipes":
        for recipe in load_recipes():
            print(f"{recipe.slug}\t{recipe.title}")
        return 0
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
