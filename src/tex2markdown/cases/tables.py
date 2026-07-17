"""Normalize structural TeX table syntax before cell-aware rendering."""

from __future__ import annotations

import base64
import re

from .. import _legacy as legacy

FORMAL_TABLE_ENV = "formalrawtable"


def protect_formal_tables(text: str, definitions: str = "") -> str:
    for start, end in reversed(_table_spans(text)):
        block = text[start:end]
        if not _is_formal_system(block):
            continue
        block = _expand_simple_macros(block, definitions)
        encoded = base64.b64encode(block.encode("utf-8")).decode("ascii")
        replacement = rf"\begin{{{FORMAL_TABLE_ENV}}}{encoded}\end{{{FORMAL_TABLE_ENV}}}"
        text = text[:start] + replacement + text[end:]
    return text


def _expand_simple_macros(block: str, definitions: str) -> str:
    macros, identity = {}, set()
    for pattern in (legacy.RE_NEWCOMMAND, legacy.RE_DEF, legacy.RE_DEFINE):
        for _, _, name, nargs, body in legacy.collect_macros(pattern, definitions):
            if nargs == 0 and len(body) <= 100 and "#" not in body:
                macros[name] = body
            elif nargs == 1 and _mode_guard_body(body).strip() == "#1":
                identity.add(name)
    for _ in range(4):
        before = block
        for name, body in macros.items():
            block = re.sub(re.escape(name) + r"(?![A-Za-z])", lambda _: "{" + body + "}", block)
        for name in identity:
            block = _expand_identity_macro(block, name)
        if block == before:
            break
    return block


def _mode_guard_body(body: str) -> str:
    return re.sub(
        r"\\relax\s*\\ifmmode\s*(.*?)\\else\s*\\errmessage\s*\{[^{}]*\}\s*\\fi",
        r"\1", body, flags=re.DOTALL,
    )


def _expand_identity_macro(text: str, name: str) -> str:
    pattern = re.compile(re.escape(name) + r"(?![A-Za-z])\s*\{")
    for match in reversed(list(pattern.finditer(text))):
        opening = match.end() - 1
        close = legacy.find_matching_brace(text, opening)
        if close >= 0:
            text = text[:match.start()] + text[opening + 1:close] + text[close + 1:]
    return text


def decode_formal_table(block: str) -> str:
    match = re.search(
        rf"\\begin\{{{FORMAL_TABLE_ENV}\}}(.*?)\\end\{{{FORMAL_TABLE_ENV}\}}",
        block, re.DOTALL,
    )
    if not match:
        return block
    source = base64.b64decode(match.group(1)).decode("utf-8")
    caption = _formal_table_caption(source)
    cleaned = _clean_formal_table_shell(source)
    return f"*Table: {caption}*\n\n{cleaned}" if caption else cleaned


def _formal_table_caption(source: str) -> str:
    match = legacy.RE_CAPTION_COMMAND.search(source)
    if not match:
        return ""
    close = legacy.find_matching_brace(source, match.end() - 1)
    if close < 0:
        return ""
    caption = legacy.RE_LABEL_COMMAND.sub("", source[match.end():close])
    return re.sub(r"\s+", " ", caption).strip()


def _clean_formal_table_shell(source: str) -> str:
    source = legacy.RE_COMMENT_LINE.sub("", source)
    source = legacy.remove_latex_caption_commands(source)
    source = legacy.RE_LABEL_COMMAND.sub("", source)
    source = re.sub(
        r"\\begin\{(?:table\*?|center|minipage|fboxenv)\}(?:\[[^\]]*\])?(?:\{[^{}]*\})?"
        r"|\\end\{(?:table\*?|center|minipage|fboxenv)\}", "\n", source, flags=re.IGNORECASE,
    )
    item_macros = re.findall(
        r"\\def\s*(\\[A-Za-z]+)\s*\{\s*\\item(?:\s*\[[^\]]*\])?\s*\}", source
    )
    source = re.sub(
        r"\\def\s*\\[A-Za-z]+\s*\{\s*\\item(?:\s*\[[^\]]*\])?\s*\}", "", source
    )
    for name in item_macros:
        source = re.sub(re.escape(name) + r"(?![A-Za-z])\s*", "\n- ", source)
    source = re.sub(r"\\fbox\s*\{", "", source)
    source = re.sub(r"\\(?:vspace|hspace)\*?\s*\{[^{}]*\}|\\(?:bigskip|medskip|smallskip)\b", " ", source)
    source = re.sub(r"\\(?:centering|noindent)\b", " ", source)
    source = re.sub(r"\{\\bf\s+(Axioms?|Rules?)\}", r"### \1", source,
                    flags=re.IGNORECASE)
    source = re.sub(r"\\(?:begin|end)\{(?:enumerate|itemize)\}", "\n", source)
    source = re.sub(r"\\emph\s*\{([^{}]*)\}", r"*\1*", source)
    source = re.sub(r"\\item\b\s*", "\n- ", source)
    source = re.sub(r"(?m)^\s*\}\s*$", "", source)
    return re.sub(r"\n{3,}", "\n\n", source).strip()


def _is_formal_system(block: str) -> bool:
    labels = len(re.findall(r"\\item\b", block))
    rules = bool(re.search(r"(?i)\b(?:axioms?|inference\s+rules?|rules?)\b", block))
    formulas = len(re.findall(r"\$|\\(?:frac|to|Box|land|lor|neg)\b", block))
    definitions = bool(re.search(r"(?i)\bformal\s+definitions?\b", block))
    bracket_formulas = len(re.findall(
        r"\\[A-Za-z]+\s*\[[^\]]*\\(?:leq|geq|neq|not|equiv|sim|prec|succ)\b",
        block,
    ))
    formal_clauses = len(re.findall(
        r"(?m)^\s*\\[A-Z][A-Z0-9]*\s+\\[A-Za-z]+\s*\[",
        block,
    ))
    return (labels >= 3 and rules and formulas >= 3) or (
        definitions and bracket_formulas >= 2 and formal_clauses >= 2
    )


def _table_spans(text: str) -> list[tuple[int, int]]:
    token = re.compile(r"\\(begin|end)\s*\{(table\*?)\}", re.IGNORECASE)
    stack, spans = [], []
    for match in token.finditer(text):
        if match.group(1).lower() == "begin":
            stack.append((match.group(2).lower(), match.start()))
            continue
        index = next((i for i in range(len(stack) - 1, -1, -1)
                      if stack[i][0] == match.group(2).lower()), None)
        if index is not None:
            _, start = stack.pop(index)
            spans.append((start, match.end()))
    return spans


def normalize_body(body: str) -> str:
    body = re.sub(r"(?<=\d)\\\.(?=\d)", ".", body)
    body = re.sub(r"\\cr\b", r"\\\\", body)
    body = re.sub(r"\\(?:noalign|omit)\s*\{[^{}]*\}", "", body)
    return expand_multicolumns(body)


def should_preserve_source(block: str) -> bool:
    nested = len(re.findall(r"\\begin\{tabular\*?\}", block, re.IGNORECASE)) > 1
    fragile_layout = bool(re.search(
        r"\\(?:shortstack|fbox|parbox|char\d+|bordermatrix)\b|\\\|", block,
        re.IGNORECASE,
    ))
    custom_pairs = re.findall(r"\\[A-Z][A-Za-z]+\s*\{[^{}]*\}\s*\{[^{}]*\}", block)
    grouped_headers = len(re.findall(r"\\multicolumn\s*\{", block, re.IGNORECASE)) >= 3
    old_math_styles = len(re.findall(r"\$[^$]*\{\\(?:it|bf|rm)\b", block)) >= 2
    return nested or fragile_layout or grouped_headers or old_math_styles or len(custom_pairs) >= 2


def source_table_content(block: str) -> str:
    block = legacy.remove_latex_caption_commands(block)
    block = legacy.RE_LABEL_COMMAND.sub("", block)
    block = re.sub(r"\\begin\{table\*?\}(?:\[[^\]]*\])?|\\end\{table\*?\}", "", block,
                   flags=re.IGNORECASE)
    block = re.sub(r"\\begin\{center\}|\\end\{center\}", "", block, flags=re.IGNORECASE)
    block = re.sub(r"(?<=\d)\\\.(?=\d)", ".", block)
    return block.strip()


def expand_multicolumns(text: str) -> str:
    starts = list(re.finditer(r"\\multicolumn\s*", text))
    for match in reversed(starts):
        arguments = _balanced_arguments(text, match.end(), 3)
        if not arguments or not arguments[0][2].strip().isdigit():
            continue
        span = max(1, int(arguments[0][2].strip()))
        label = arguments[2][2]
        replacement = label + (" & " * (span - 1))
        text = text[:match.start()] + replacement + text[arguments[2][1] + 1:]
    return text


def _balanced_arguments(text: str, cursor: int, count: int) -> list[tuple[int, int, str]]:
    arguments = []
    for _ in range(count):
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] != "{":
            return []
        close = legacy.find_matching_brace(text, cursor)
        if close < 0:
            return []
        arguments.append((cursor, close, text[cursor + 1:close]))
        cursor = close + 1
    return arguments


def strip_cell_spacing(cell: str) -> str:
    cell = re.sub(r"\\(?:quad|qquad|enspace|thinspace)\b|\\[,;!]", " ", cell)
    cell = re.sub(r"\\(?:vskip|hskip|kern)\s*[-+]?\s*[\d.]+(?:pt|mm|cm|em|ex)\b", " ", cell)
    cell = re.sub(r"\[\s*[-+]?\d*\.?\d+\s*(?:pt|mm|cm|em|ex)\s*\]", " ", cell)
    return cell
