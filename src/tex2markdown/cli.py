"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .api import Tex2MarkdownError, convert, convert_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tex2markdown", description="Convert scientific LaTeX to retrieval-ready Markdown."
    )
    parser.add_argument("input", help="A .tex file, project directory, or - for stdin")
    parser.add_argument("-o", "--output", default="-", help="Markdown output path (default: stdout)")
    parser.add_argument("--main-file", help="Main TeX filename for a project or bundle")
    parser.add_argument("--date", default=r"\today", help=r"Deterministic expansion for \today")
    parser.add_argument("--metadata", help="Optional conversion metadata JSON path, or - for stdout")
    args = parser.parse_args()
    if args.output == "-" and args.metadata == "-":
        parser.error("Markdown and metadata cannot both be written to stdout")
    return args


def write_text(destination: str, text: str) -> None:
    if destination == "-":
        sys.stdout.write(text)
    else:
        Path(destination).write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    try:
        if args.input == "-":
            result = convert(sys.stdin.read(), conversion_date=args.date)
        else:
            result = convert_path(args.input, main_file=args.main_file, conversion_date=args.date)
    except (Tex2MarkdownError, OSError) as error:
        raise SystemExit(f"tex2markdown: {error}") from error
    write_text(args.output, result.markdown)
    if args.metadata:
        payload = json.dumps(result.to_dict(include_markdown=False), indent=2) + "\n"
        write_text(args.metadata, payload)


if __name__ == "__main__":
    main()
