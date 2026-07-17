from __future__ import annotations

from pathlib import Path

import pytest

from tex2markdown import (
    PaperMetadata,
    SourceSelectionError,
    UnsupportedFormatError,
    convert,
    convert_bundle,
    convert_path,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_convert_source_preserves_math_and_removes_figure() -> None:
    result = convert((FIXTURES / "simple.tex").read_text(encoding="utf-8"))
    assert "# A Synthetic Paper" in result.markdown
    assert "$x^2$" in result.markdown
    assert "Not retained" not in result.markdown
    assert "plot.pdf" not in result.markdown
    assert result.selected_file == "source.tex"


def test_convert_bundle_expands_input_and_honors_main_file() -> None:
    files = {
        "other.tex": r"\documentclass{article}\begin{document}" + "other " * 400 + r"\end{document}",
        "main.tex": r"\documentclass{article}\title{Main}\begin{document}\input{parts/body}\end{document}",
        "parts/body.tex": r"\section{Finding} Bundle evidence is retained.",
    }
    result = convert_bundle(files, main_file="main.tex")
    assert result.selected_file == "main.tex"
    assert "Bundle evidence is retained." in result.markdown
    assert result.source_file_count == 3


def test_convert_path_directory_and_metadata_fallback(tmp_path: Path) -> None:
    source = tmp_path / "paper.tex"
    source.write_text(r"\documentclass{article}\begin{document}" + "evidence " * 400 + r"\end{document}")
    result = convert_path(tmp_path, metadata=PaperMetadata(title="Fallback title"))
    assert result.markdown.startswith("# Fallback title")
    assert result.to_dict(include_markdown=False)["selected_file"] == "paper.tex"


def test_support_only_bundle_has_typed_error() -> None:
    with pytest.raises(SourceSelectionError):
        convert_bundle({"only.sty": r"\ProvidesPackage{x}\newcommand{\x}{x}"})


def test_html_has_typed_unsupported_format_error() -> None:
    with pytest.raises(UnsupportedFormatError):
        convert("<html><body>not TeX</body></html>")


def test_today_is_deterministic_and_configurable() -> None:
    source = (r"\documentclass{article}\title{Date test}\begin{document}"
              r"\begin{abstract}Compiled \today.\end{abstract}Body.\end{document}")
    preserved = convert(source).markdown
    expanded = convert(source, conversion_date="July 16, 2026").markdown
    assert r"\today" in preserved
    assert "July 16, 2026" in expanded
