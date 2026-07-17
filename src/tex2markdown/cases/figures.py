"""Retain source-native formal content embedded in figure containers."""

from __future__ import annotations

import re
from collections.abc import Callable

from .. import _legacy as legacy

IN_SCOPE = re.compile(
    r"\\begin\{(?:verbatim|alltt|lstlisting|tabbing|tabular|array|algorithm|algorithmic|program|"
    r"equation|align|eqnarray|gather|multline|displaymath|cases|quote)\*?\}"
    r"|\\(?:parbox|shortex|eenumsentence|ordinalg|texttt)\b|\\\[|\$\$"
    r"|\\par\\(?:quad|qquad)|\{\\bf\s+(?:begin|for|if|while|return)\}"
    r"|\{\s*(?:begin|for|if|while|return|elseif|else|end)\s*\}",
    re.IGNORECASE,
)


def render_embedded_content(block: str, render_body: Callable[[str], str]) -> str:
    if re.search(r"\\begin\s*\{(?:picture|pspicture)\}", block, re.IGNORECASE):
        formal = formal_picture_content(block)
        return f"\n\n### Source-native formal content\n\n```text\n{formal}\n```\n\n" if formal else ""
    if not IN_SCOPE.search(block) and not meaningful_text_body(block):
        return ""
    body = legacy.remove_latex_caption_commands(block)
    body = legacy.RE_LABEL_COMMAND.sub("", body)
    body = re.sub(r"\\(?:begin|end)\{figure\*?\}", "", body, flags=re.IGNORECASE)
    body = re.sub(r"^\s*\[(?:h|t|b|p|!)+\]", "", body, flags=re.IGNORECASE)
    formal_definitions = formal_graph_definitions(body)
    body = drop_graphic_definitions(body)
    body = drop_psfrag_commands(body)
    body = drop_external_graphics(body)
    body = re.sub(r"\\(?:fuline|centering)\b", " ", body)
    body = re.sub(r"(?m)^\s*\$\$\s*(?:\\qquad\s*)?\$\$\s*$", "", body)
    body = _unwrap_command(body, "ordinalg")
    rendered = render_body(body).strip()
    if formal_definitions:
        rendered = "### Source-native formal definitions\n\n" + formal_definitions + "\n\n" + rendered
    return f"\n\n{rendered}\n\n" if rendered else ""


def formal_picture_content(block: str) -> str:
    math = re.compile(r"(?<!\\)\$(?!\$)(.*?)(?<!\\)\$", re.DOTALL)
    signal = re.compile(r"\\(?:leftarrow|langle|attr|tt|bot)\b|:-")
    values = []
    for match in math.finditer(block):
        value = re.sub(r"\s+", " ", match.group(1)).strip()
        if signal.search(value) and value not in values:
            values.append(f"${value}$")
    return "\n".join(values) if len(values) >= 2 else ""


def meaningful_text_body(block: str) -> bool:
    visual = r"\\(?:includegraphics|epsfig|psfig|xymatrix|pstree)\b|\\begin\{(?:frame)?graph\}"
    if re.search(visual, block, re.IGNORECASE) and not IN_SCOPE.search(block):
        return False
    body = legacy.remove_latex_caption_commands(block)
    body = legacy.RE_LABEL_COMMAND.sub("", body)
    body = re.sub(r"\\(?:begin|end)\{figure\*?\}", "", body, flags=re.IGNORECASE)
    body = re.sub(r"^\s*\[(?:h|t|b|p|!)+\]", "", body, flags=re.IGNORECASE)
    body = drop_graphic_definitions(body)
    body = drop_psfrag_commands(body)
    body = drop_external_graphics(body)
    return len(re.findall(r"[A-Za-z]{3,}|[$_^]", body)) >= 5


def drop_graphic_definitions(text: str) -> str:
    pattern = re.compile(r"\\(?:re)?newcommand\s*\{?\\[A-Za-z@]+\}?", re.IGNORECASE)
    for match in reversed(list(pattern.finditer(text))):
        cursor = match.end()
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor < len(text) and text[cursor] == "[":
            close = text.find("]", cursor + 1)
            cursor = close + 1 if close >= 0 else cursor
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] != "{":
            continue
        close = legacy.find_matching_brace(text, cursor)
        if close >= 0 and re.search(r"\\begin\{(?:frame)?graph|\\begin\{picture", text[cursor:close]):
            text = text[:match.start()] + text[close + 1:]
    return text


def formal_graph_definitions(text: str) -> str:
    if "::=" not in text or "tabular" not in text:
        return ""
    pattern = re.compile(r"\\(?:re)?newcommand\s*\{?\\[A-Za-z@]+\}?", re.IGNORECASE)
    definitions = []
    for match in pattern.finditer(text):
        cursor = match.end()
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor < len(text) and text[cursor] == "[":
            close = text.find("]", cursor + 1)
            cursor = close + 1 if close >= 0 else cursor
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] != "{":
            continue
        close = legacy.find_matching_brace(text, cursor)
        raw = text[match.start():close + 1] if close >= 0 else ""
        if re.search(r"\\begin\{(?:frame)?graph", raw):
            definitions.append(raw.strip())
    return "\n\n".join(definitions)


def drop_psfrag_commands(text: str) -> str:
    pattern = re.compile(r"\\psfrag\s*\{", re.IGNORECASE)
    for match in reversed(list(pattern.finditer(text))):
        first = legacy.find_matching_brace(text, match.end() - 1)
        cursor = _skip_optional_arguments(text, first + 1)
        if first < 0 or cursor >= len(text) or text[cursor] != "{":
            continue
        second = legacy.find_matching_brace(text, cursor)
        if second >= 0:
            text = text[:match.start()] + text[second + 1:]
    return text


def _skip_optional_arguments(text: str, cursor: int) -> int:
    while True:
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] != "[":
            return cursor
        close = text.find("]", cursor + 1)
        if close < 0:
            return cursor
        cursor = close + 1


def drop_external_graphics(text: str) -> str:
    pattern = re.compile(r"\\(?:includegraphics|epsfig|psfig|epsfbox)\*?\b", re.IGNORECASE)
    for match in reversed(list(pattern.finditer(text))):
        parsed = _read_one_argument(text, match.end())
        if parsed:
            text = text[:match.start()] + text[parsed:]
    return text


def _unwrap_command(text: str, name: str) -> str:
    pattern = re.compile(rf"\\{re.escape(name)}\s*\{{", re.IGNORECASE)
    for match in reversed(list(pattern.finditer(text))):
        close = legacy.find_matching_brace(text, match.end() - 1)
        if close >= 0:
            text = text[:match.start()] + text[match.end():close] + text[close + 1:]
    return text


def _read_one_argument(text: str, position: int) -> int | None:
    while position < len(text) and text[position].isspace():
        position += 1
    if position >= len(text) or text[position] != "{":
        return None
    close = legacy.find_matching_brace(text, position)
    return close + 1 if close >= 0 else None
