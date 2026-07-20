# tex2markdown

`tex2markdown` converts a LaTeX document or project to one Markdown string. It
preserves LaTeX math and fragile formal content, converts suitable data tables,
expands local inputs and macros, and removes figures, captions, image commands,
and bibliographies.

The package is standalone. Its renderer, project selection, and bundled-source
expansion are private `tex2markdown` modules; it does not import or require
ClaimSpy's retrieval pipeline or the repository's archived formal converter.

## Install

```bash
pip install tex2markdown
```

## Python API

Convert one in-memory document:

```python
from tex2markdown import convert

markdown = convert(r"""
\documentclass{article}
\title{A Small Example}
\begin{document}
\maketitle
\section{Result}
The value is $x^2$.
\end{document}
""")
```

Strings passed to `convert()` are always interpreted as LaTeX source, never as
file paths. For a file or a multi-file project, use `convert_path()`:

```python
from tex2markdown import convert_path

markdown = convert_path("paper.tex")
markdown = convert_path("project/")
markdown = convert_path("project/", main_file="main.tex")
```

A directory is scanned recursively. Hidden and version-control paths, common
binary formats, non-UTF-8 files, and files larger than 20 MB are skipped. The
main TeX document is selected automatically unless `main_file` is supplied.
Nested `\input` and `\include` files and referenced local style macros are
expanded before conversion.

Both functions return `str`. Titles and abstracts come only from LaTeX source;
documents without a title use `# Untitled`. The `\today` command is preserved
literally, so repeated conversion is deterministic.

## Command line

```bash
tex2markdown paper.tex
tex2markdown paper.tex -o paper.md
tex2markdown project/ --main-file main.tex
cat paper.tex | tex2markdown -
```

Markdown is written to standard output unless `-o` is supplied. Standard input
and individual files do not accept `--main-file`.

## Errors

Conversion failures derive from `tex2markdown.ConversionError`. More specific
types are available for invalid filesystem input, unsupported formats, and main
source selection: `InputError`, `UnsupportedFormatError`, and
`SourceSelectionError`.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv build
```

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
