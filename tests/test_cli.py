from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def document(title: str) -> str:
    return (
        rf"\documentclass{{article}}\title{{{title}}}"
        r"\begin{document}Body.\end{document}"
    )


def run_cli(*arguments: str, source: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tex2markdown.cli", *arguments],
        input=source,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_writes_markdown(tmp_path: Path) -> None:
    source_path = tmp_path / "paper.tex"
    output_path = tmp_path / "paper.md"
    source_path.write_text(document("Output File"), encoding="utf-8")
    completed = run_cli(str(source_path), "-o", str(output_path))
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == ""
    assert "# Output File" in output_path.read_text(encoding="utf-8")


def test_cli_reads_stdin() -> None:
    completed = run_cli("-", source=document("Standard Input"))
    assert completed.returncode == 0, completed.stderr
    assert "# Standard Input" in completed.stdout
