# tex2markdown

Source-preserving LaTeX-to-Markdown conversion for scientific papers.

`tex2markdown` converts prose and document structure into readable Markdown while retaining
LaTeX math and fragile formal content when conversion could change its meaning. It supports
single TeX files, directory-based projects, and scholarweave-style source bundles.

The converter has been validated on a large corpus of scientific papers. It deliberately
removes external figures and captions; it does not download images, perform OCR, or treat a
nonempty document as sufficient evidence of a safe conversion.

## Install

```bash
pip install tex2markdown
```

## Python API

```python
from tex2markdown import convert_path

result = convert_path("paper/")
print(result.markdown)
print(result.risk_flags)
```

For in-memory multi-file projects:

```python
from tex2markdown import convert_bundle

result = convert_bundle(
    {
        "main.tex": r"\documentclass{article}\begin{document}\input{body}\end{document}",
        "body.tex": r"\section{Result} The value is $x^2$.",
    },
    main_file="main.tex",
)
```

## CLI

```bash
tex2markdown paper.tex -o paper.md
tex2markdown paper-directory/ -o paper.md --metadata conversion.json
cat paper.tex | tex2markdown -
```

For reproducibility, `\today` remains source LaTeX unless explicitly expanded with
`--date "July 16, 2026"` or the corresponding `conversion_date` API argument.

The optional metadata JSON records the selected source, conversion method, warnings, risk
flags, and structural inventories. These signals support review and triage; they are not a
proof of semantic equivalence.

## Conversion policy

- Preserve inline and display math as LaTeX.
- Convert headings, lists, prose, and suitable data tables to Markdown.
- Preserve fragile formal systems, algorithms, and complex tables as fenced LaTeX.
- Remove external graphics, figure environments, and captions.
- Retain substantive appendices and source-local macro definitions needed by the output.
- Report suspicious losses through warnings, risk flags, and retrieval status.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv build
```

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
