"""Command-line interface for tex2markdown."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .api import convert, convert_path
from .exceptions import ConversionError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tex2markdown", description="Convert LaTeX to Markdown.")
    parser.add_argument("input", metavar="FILE_OR_FOLDER")
    parser.add_argument("-o", "--output", type=Path, help="write Markdown to this file")
    parser.add_argument("--main-file", help="main TeX file relative to a project folder")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.input == "-":
            if args.main_file is not None:
                raise ConversionError("--main-file is only valid for folder input")
            markdown = convert(sys.stdin.read())
        else:
            markdown = convert_path(args.input, main_file=args.main_file)
        _write_output(markdown, args.output)
    except (ConversionError, OSError) as error:
        parser.error(str(error))
    return 0


def _write_output(markdown: str, output: Path | None) -> None:
    if output is None:
        sys.stdout.write(markdown)
    else:
        output.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
