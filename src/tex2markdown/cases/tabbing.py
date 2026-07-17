"""Render TeX tabbing layouts as stable line-oriented text."""

from __future__ import annotations

import re
from collections.abc import Callable


def render(block: str, clean_code: Callable[[str], str]) -> str:
    body = re.sub(r"^.*?\\begin\{tabbing\}", "", block, count=1, flags=re.DOTALL)
    body = re.sub(r"\\end\{tabbing\}.*$", "", body, count=1, flags=re.DOTALL)
    body = re.sub(r"(?m)^.*\\kill\s*$", "", body)
    body = re.sub(r"\\\\\s*\[[^\]]*\]", r"\\\\", body)
    body = body.replace(r"\>", "  ").replace(r"\=", "")
    body = re.sub(r"\{\\(?:bf|it|sf|tt)\s+([^{}]*)\}", r"\1", body)
    body = clean_code(body)
    lines = [line.rstrip() for line in body.splitlines() if line.strip()]
    body = "\n".join(lines)
    return f"\n\n```text\n{body}\n```\n\n" if body else ""
