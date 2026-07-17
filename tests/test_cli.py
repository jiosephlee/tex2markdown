from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_writes_markdown_and_metadata(tmp_path: Path) -> None:
    markdown, metadata = tmp_path / "paper.md", tmp_path / "paper.json"
    completed = subprocess.run(
        [sys.executable, "-m", "tex2markdown.cli", str(FIXTURES / "simple.tex"),
         "-o", str(markdown), "--metadata", str(metadata)],
        check=False, capture_output=True, text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "A Synthetic Paper" in markdown.read_text(encoding="utf-8")
    assert json.loads(metadata.read_text(encoding="utf-8"))["selected_file"] == "simple.tex"
